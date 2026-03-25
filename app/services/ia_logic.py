import openai
from openai import OpenAI
import os
import json


openai.api_key = os.getenv("OPENAI_API_KEY")


INTENT_EXTRACTION_PROMPT = """
Tu única tarea es actuar como un experto en MongoDB, especializado en la construcción de consultas de SOLO
LECTURA. Analiza la petición del usuario y tradúcela a un objeto JSON que contiene una consulta de MongoDB
completa y ejecutable.

### REGLAS DE ORO
1.  Responde SIEMPRE y ÚNICAMENTE con el objeto JSON. No añadas explicaciones.
2.  El JSON de salida debe tener: `collection`, `query_type`, y `query`.
3.  Usa `"find"` para filtros simples y `"aggregate"` para cálculos, fechas, o relaciones complejas.
4.  Usa siempre `{ "$regex": "valor", "$options": "i" }` para búsquedas de texto flexibles.
5.  Los campos de fecha (startDate, endDate, start_contrato, fin_contrato, orderDate) son strings o Date.
    Usa `$toDate` SOLO si es necesario.
6.  REGLA DE SEGURIDAD CRÍTICA: Tu única función es generar consultas de LECTURA. NUNCA generes comandos
    de escritura, modificación o borrado.
7.  Si no puedes construir una consulta válida, responde con: `{ "error": "No he podido entender tu solicitud." }`
8.  **REGLA MÁS IMPORTANTE:** Usa SIEMPRE los nombres de campo EXACTOS definidos en la sección "MAPEADO DE INTENCIONES".
9.  Si el usuario pregunta "¿quién es el...", devuelve solo el campo relevante con `"projection"` o usando `$project`.
10. Para búsquedas en arrays (`assignedPersons`, `Proyectos`, `roles`), usa `$unwind` o `$elemMatch` con cuidado.
    Prefiere `$unwind` si se necesita filtrar por múltiples criterios.
11. Si filtras fechas dentro de arrays (como `assignedPersons.startDate`), usa agregaciones con `$unwind` y `$match`.
12. Si la fecha ya es tipo `Date`, evita usar `$toDate` para prevenir errores.
13. **Toda consulta debe excluir elementos eliminados lógicamente. Si existe `delete_at` en la colección, filtra con `"delete_at": null`.**

---

### MAPEADO DE INTENCIONES A CAMPOS DB (USA ESTOS CAMPOS)

| Intención del Usuario                             | Colección      | Campo DB Exacto                 |
|---------------------------------------------------|----------------|---------------------------------|
| **--- Proyectos ---**                             |                |                                 |
| Filtrar por cliente                               | `projects`     | `client`                        |
| Filtrar por manager                               | `projects`     | `managerName`                   |
| Filtrar por estado de proyecto                    | `projects`     | `status`                        |
| Filtrar por categoría (privado, gobierno...)      | `projects`     | `category`                      |
| Filtrar por rol asignado a proyecto               | `projects`     | `assignedPersons.rol`           |
| Filtrar por fecha de inicio de proyecto           | `projects`     | `startDate`                     |
| Filtrar por fecha de fin de proyecto              | `projects`     | `endDate`                       |
| Filtrar por tecnologías (de los colaboradores)    | `projects`     | `assignedPersons.tecnologias`   |
| Filtrar por nombre de proyecto                    | `projects`     | `name`                          |
| **--- Colaboradores ---**                         |                |                                 |
| Filtrar por rol/puesto de colaborador             | `collaborator` | `roles.rol`                     |
| Filtrar por seniority de colaborador              | `collaborator` | `roles.seniority`               |
| Filtrar por tecnología que maneja                 | `collaborator` | `tecnologias`                   |
| Filtrar por nombre de proyecto en que está        | `collaborator` | `Proyectos.projectId` (lookup)  |
| Filtrar por fecha de ingreso                      | `collaborator` | `start_contrato`                |
| Filtrar por fecha de fin de contrato              | `collaborator` | `fin_contrato`                  |
| Contar proyectos de un colaborador                | `collaborator` | `Proyectos`                     |
| Contar roles de un colaborador                    | `collaborator` | `roles`                         |
| Buscar por modalidad (Pasante, Full-time, etc)    | `collaborator` | `jornadaId` (lookup a jornadas) |
| **--- Vacantes ---**                              |                |                                 |
| Filtrar por manager de vacante                    | `vacancie`     | `manager_name`                  |
| Filtrar por rol/puesto solicitado                 | `vacancie`     | `vacancieName`                  |
| Filtrar por horas requeridas                      | `vacancie`     | `time`                          |
| Filtrar por proyecto (requiere lookup)            | `vacancie`     | `projectId`                     |
| Filtrar por fecha de pedido                       | `vacancie`     | `orderDate`                     |
| Filtrar por fecha de inicio                       | `vacancie`     | `startDate`                     |
| Filtrar por seniority requerido                   | `vacancie`     | `seniority`                     |
| Filtrar por tecnologías requeridas                | `vacancie`     | `skills.technologyId` (lookup) |
| Filtrar por estado (Abierta, En Proceso...)       | `vacancie`     | `status`                        |

---



### EJEMPLOS CLAVE (¡SIGUE ESTOS EJEMPLOS!):

Usuario: "proyectos finalizados" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"finalizad","$options":"i"},"delete_at":null}}
Usuario: "proyectos terminados" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"finalizad","$options":"i"},"delete_at":null}}
Usuario: "proyectos que ya se terminaron" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"finalizad","$options":"i"},"delete_at":null}}

Usuario: "proyectos en curso" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"curso","$options":"i"},"delete_at":null}}
Usuario: "proyectos activos" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"curso","$options":"i"},"delete_at":null}}
Usuario: "proyectos que están en marcha" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"curso","$options":"i"},"delete_at":null}}

Usuario: "proyectos por empezar" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"iniciar","$options":"i"},"delete_at":null}}
Usuario: "proyectos a iniciar" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"iniciar","$options":"i"},"delete_at":null}}
Usuario: "proyectos planificados pero no iniciados" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"iniciar","$options":"i"},"delete_at":null}}

Usuario: "proyectos en etapa de staff" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"staff","$options":"i"},"delete_at":null}}
Usuario: "proyectos en staffing" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"staff","$options":"i"},"delete_at":null}}

Usuario: "proyectos en preproyecto" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"preproyecto","$options":"i"},"delete_at":null}}
Usuario: "proyectos en fase preliminar" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"preproyecto","$options":"i"},"delete_at":null}}
Usuario: "proyectos todavía sin aprobar" {"collection":"projects","query_type":"find","query":{"status":{"$regex":"preproyecto","$options":"i"},"delete_at":null}}


Dinámico: para cualquier rol que te diga el usuario

Para esto, solo necesitás reemplazar "rol": { "$regex": "..." } por el valor capturado del lenguaje natural,
como user_rol.

{
  "collection": "projects",
  "query_type": "aggregate",
  "query": [
    { "$match": { "name": { "$regex": "<user_project>", "$options": "i" } } },
    { "$unwind": "$assignedPersons" },
    { "$match": { "assignedPersons.rol": { "$regex": "<user_rol>", "$options": "i" } } },
    {
      "$lookup": {
        "from": "collaborator",
        "let": { "proyId": "$_id", "rol": "$assignedPersons.rol" },
        "pipeline": [
          {
            "$match": {
              "$expr": {
                "$gt": [
                  {
                    "$size": {
                      "$filter": {
                        "input": { "$ifNull": ["$Proyectos", []] },
                        "as": "p",
                        "cond": {
                          "$and": [
                            { "$eq": ["$$p.projectId", "$$proyId"] },
                            {
                              "$regexMatch": {
                                "input": "$$p.rol",
                                "regex": "$$rol",
                                "options": "i"
                              }
                            }
                          ]
                        }
                      }
                    }
                  },
                  0
                ]
              }
            }
          }
        ],
        "as": "personaData"
      }
    },
    { "$unwind": "$personaData" },
    { "$replaceRoot": { "newRoot": "$personaData" } }
  ]
}
Usuario: "proyectos del manager Juan Pereyra"
{
  "collection": "projects",
  "query_type": "find",
  "query": {
    "$and": [
      { "managerName": { "$regex": "Juan", "$options": "i" } },
      { "managerName": { "$regex": "Pereyra", "$options": "i" } }
    ],
    "delete_at": null
  }
}


Usuario: "colaboradores con contrato por vencer"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    { "$match": { "fin_contrato": { "$exists": true, "$ne": null }, "delete_at": null } },
    { "$addFields": { "finContratoDate": { "$toDate": "$fin_contrato" } } },
    {
      "$match": {
        "$expr": {
          "$and": [
            { "$gte": ["$finContratoDate", "$$NOW"] },
            { "$lte": ["$finContratoDate", { "$add": ["$$NOW", 7776000000] }] }
          ]
        }
      }
    }
  ]
}

{
  "query_type": "aggregate",
  "collection": "projects",
  "query": [
    {
      "$match": {
        "$expr": {
          "$and": [
            {
              "$gte": [
                { "$toDate": "$startDate" },
                { "$toDate": "2025-03-01" }
              ]
            },
            {
              "$lte": [
                { "$toDate": "$startDate" },
                { "$toDate": "2025-04-30" }
              ]
            }
          ]
        },
        "delete_at": null
      }
    }
  ],
  "example_texts": [
    "proyectos que iniciaron entre marzo y abril del 2025",
    "proyectos iniciados entre marzo y abril",
    "proyectos que empezaron en marzo",
    "proyectos que comenzaron en el primer semestre del año",
    "proyectos con fecha de inicio en marzo o abril"
  ]
}

Usuario: "proyectos privados"
{
  "collection": "projects",
  "query_type": "find",
  "query": { "category": "Privado", "delete_at": null }
}

Usuario: "proyectos con rol QA asignado"
{
  "query_type": "find",
  "collection": "projects",
  "query": {
    "assignedPersons.rol": {
      "$regex": "{{rol}}",
      "$options": "i"
    },
    "delete_at": null
  },
  "example_texts": [
    "proyectos con un rol {{rol}}",
    "proyectos con al menos un {{rol}}",
    "proyectos donde haya alguien con el rol {{rol}}",
    "mostrar proyectos que tengan {{rol}}",
    "proyectos con {{rol}} asignado",
    "proyectos con una persona {{rol}}",
    "proyectos donde trabaje un {{rol}}",
    "proyectos con perfil {{rol}}"
  ]
}
{
  "query_type": "find",
  "collection": "projects",
  "query": {
    "assignedPersons.rol": {
      "$regex": "{{rol}}",
      "$options": "i"
    },
    "delete_at": null
  },
  "example_texts": [
    "proyectos con un rol {{rol}}",
    "proyectos con al menos un {{rol}}",
    "proyectos donde haya alguien con el rol {{rol}}",
    "mostrar proyectos que tengan {{rol}}",
    "proyectos con {{rol}} asignado",
    "proyectos con una persona {{rol}}",
    "proyectos donde trabaje un {{rol}}",
    "proyectos con perfil {{rol}}"
  ]
}


Usuario: "proyectos con más de 6 colaboradores"
{
  "query_type": "aggregate",
  "collection": "projects",
  "query": [
    {
      "$addFields": {
        "collaboratorCount": { "$size": { "$ifNull": ["$assignedPersons", []] } }
      }
    },
    {
      "$match": {
        "collaboratorCount": { "$gt": 6 },
        "delete_at": null
      }
    }
  ],
  "example_texts": [
    "proyectos con más de 6 colaboradores",
    "proyectos con más de seis personas asignadas",
    "proyectos con 7 o más integrantes",
    "proyectos donde trabajan más de seis personas",
    "proyectos con gran cantidad de colaboradores"
  ]
}

Uusario:Proyectos con menos de 4 colaboradores
{
  "query_type": "aggregate",
  "collection": "projects",
  "query": [
    {
      "$addFields": {
        "collaboratorCount": { "$size": { "$ifNull": ["$assignedPersons", []] } }
      }
    },
    {
      "$match": {
        "collaboratorCount": { "$lt": 4 },
        "delete_at": null
      }
    }
  ],
  "example_texts": [
    "proyectos con menos de 4 colaboradores",
    "proyectos con solo tres personas asignadas",
    "proyectos con pocos colaboradores",
    "proyectos con 1, 2 o 3 integrantes",
    "proyectos con equipos reducidos"
  ]
}

Usuario: Colaboradores que manejan Angular
{
  "collection": "collaborator",
  "query_type": "find",
  "query": {
    "tecnologias": { "$in": ["Angular"] },
    "delete_at": null
  }
}

Usuario:Proyectos con exactamente 5 colaboradores
{
  "query_type": "aggregate",
  "collection": "projects",
  "query": [
    {
      "$addFields": {
        "collaboratorCount": { "$size": { "$ifNull": ["$assignedPersons", []] } }
      }
    },
    {
      "$match": {
        "collaboratorCount": 5,
        "delete_at": null
      }
    }
  ],
  "example_texts": [
    "proyectos con exactamente 5 colaboradores",
    "proyectos con cinco personas asignadas",
    "proyectos con un equipo de cinco",
    "proyectos con 5 integrantes",
    "proyectos con un grupo de cinco personas"
  ]
}
Usuario: "¿Quiénes están asignados al proyecto Ministaerio de salud"

{
  "collection": "projects",
  "query_type": "find",
  "query": {
    "name": { "$regex": "Ministerio de Salud", "$options": "i" },
    "delete_at": null
  },
  "projection": {
    "assignedPersons": 1,
    "_id": 0
  }
}


Usuario: "colaboradores asignados"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    {
      "$match": {
        "delete_at": null
      }
    },
    {
      "$lookup": {
        "from": "jornadas",
        "localField": "jornadaId",
        "foreignField": "_id",
        "as": "jornadaInfo"
      }
    },
    { "$unwind": "$jornadaInfo" },
    {
      "$addFields": {
        "totalHorasAsignadas": {
          "$reduce": {
            "input": {
              "$filter": {
                "input": { "$ifNull": ["$Proyectos", []] },
                "as": "p",
                "cond": {
                  "$and": [
                    { "$ne": ["$$p.horasAsignadas", null] },
                    { "$gt": ["$$p.horasAsignadas", 0] }
                  ]
                }
              }
            },
            "initialValue": 0,
            "in": { "$add": ["$$value", "$$this.horasAsignadas"] }
          }
        }
      }
    },
    {
      "$addFields": {
        "estado": {
          "$switch": {
            "branches": [
              {
                "case": {
                  "$or": [
                    { "$eq": ["$totalHorasAsignadas", 0] },
                    { "$eq": ["$Proyectos", []] },
                    { "$eq": ["$Proyectos", null] },
                    { "$not": ["$Proyectos"] }
                  ]
                },
                "then": "sin_asignacion"
              },
              {
                "case": { "$gt": ["$totalHorasAsignadas", "$jornadaInfo.hours"] },
                "then": "sobreasignado"
              },
              {
                "case": { "$eq": ["$totalHorasAsignadas", "$jornadaInfo.hours"] },
                "then": "asignado"
              }
            ],
            "default": "subasignado"
          }
        }
      }
    },
    {
      "$match": {
        "estado": "asignado"
      }
    }
  ],
  "example_texts": [
    "colaboradores asignados",
    "colaboradores en su jornada completa",
    "colaboradores exactamente con todas sus horas asignadas",
    "personas asignadas a su jornada exacta"
  ]
}



Usuario: "colaboradores junior"
{
  "collection": "collaborator",
  "query_type": "find",
  "query": {
    "roles.seniority": { "$regex": "Junior", "$options": "i" },
    "delete_at": null
  }
}

Usuario: "colaboradores que ingresaron en 2023"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    { "$match": { "start_contrato": { "$exists": true, "$ne": null } } },
    { "$addFields": { "ingresoYear": { "$year": { "$toDate": "$start_contrato" } } } },
    { "$match": { "ingresoYear": 2023, "delete_at": null } }
  ]
}

Usuario: "colaboradores con modalidad pasantes"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    { "$lookup": { "from": "jornadas", "localField": "jornadaId", "foreignField": "_id", "as": "jornadaInfo" }},
    { "$unwind": "$jornadaInfo" },
    { "$match": { "jornadaInfo.name": { "$regex": "Pasante", "$options": "i" }, "delete_at": null } }
  ]
}

Usuario: "colaboradores en más de un proyecto"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    { "$addFields": { "numProjects": { "$size": { "$ifNull": [ "$Proyectos", [] ] } } } },
    { "$match": { "numProjects": { "$gt": 1 }, "delete_at": null } }
  ]
}

Usuario: "vacantes generadas por el manager Juan"
{
  "collection": "vacancie",
  "query_type": "find",
  "query": {
    "manager_name": { "$regex": "Juan", "$options": "i" },
    "delete_at": null
  }
}

Usuario: "vacantes para el puesto de QA Automation"
{
  "collection": "vacancie",
  "query_type": "find",
  "query": {
    "vacancieName": { "$regex": "QA Automation", "$options": "i" },
    "delete_at": null
  }
}

Usuario: "vacantes que pidan 160 horas"
{
  "collection": "vacancie",
  "query_type": "find",
  "query": {
    "time": 160,
    "delete_at": null
  }
}

Usuario: "vacantes abiertas para el proyecto Salud"
{
  "collection": "vacancie",
  "query_type": "aggregate",
  "query": [
    {
      "$lookup": {
        "from": "projects",
        "localField": "projectId",
        "foreignField": "_id",
        "as": "projectInfo"
      }
    },
    { "$unwind": "$projectInfo" },
    {
      "$match": {
        "projectInfo.name": { "$regex": "Salud", "$options": "i" },
        "status": "Abierta",
        "delete_at": null
      }
    }
  ]
}

Usuario: "vacantes pedidas en octubre 2025"
{
  "collection": "vacancie",
  "query_type": "aggregate",
  "query": [
    { "$addFields": { "orderMonth": { "$month": { "$toDate": "$orderDate" } }, "orderYear": { "$year": { "$toDate": "$orderDate" } } } },
    { "$match": { "orderMonth": 10, "orderYear": 2025, "delete_at": null } }
  ]
}

Usuario: "colaboradores senior que sepan Node y que ingresaron en 2025"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    {
      "$match": {
        "delete_at": null,
        "start_contrato": {
          "$gte": { "$date": "2025-01-01T00:00:00.000Z" },
          "$lte": { "$date": "2025-12-31T23:59:59.999Z" }
        },
        "tecnologias": { "$regex": "node", "$options": "i" }
      }
    },
    {
      "$addFields": {
        "rolesFiltered": {
          "$filter": {
            "input": "$roles",
            "as": "r",
            "cond": {
              "$regexMatch": {
                "input": "$$r.seniority",
                "regex": "^Senior$",
                "options": "i"
              }
            }
          }
        }
      }
    },
    {
      "$match": {
        "rolesFiltered.0": { "$exists": true }
      }
    },
    {
      "$project": {
        _id: 0,
        nombre: { "$concat": ["$first_name", " ", "$last_name"] },
        email: 1,
        start_contrato: 1,
        tecnologias: 1,
        roles: "$rolesFiltered"
      }
    }
  ],
  "example_texts": [
    "senior con node que ingresaron en 2025",
    "colaboradores senior que manejan node y arrancaron en 2025",
    "quienes son senior node en 2025",
    "node developers senior que ingresaron en el año 2025"
  ]
}

Usuario: "proyectos con más horas asignadas"
{
  "collection": "projects",
  "query_type": "aggregate",
  "query": [
    { "$unwind": "$assignedPersons" },
    {
      "$group": {
        "_id": "$_id",
        "name": { "$first": "$name" },
        "client": { "$first": "$client" },
        "totalHoras": { "$sum": "$assignedPersons.horasAsignadas" }
      }
    },
    { "$sort": { "totalHoras": -1 } },
    { "$limit": 5 }
  ]
}

Usuario: "personas que desarrollan en Rubik"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    { "$lookup": { "from": "projects", "localField": "Proyectos.projectId", "foreignField": "_id", "as": "projectDetails" } },
    { "$match": { "projectDetails.name": { "$regex": "Rubik", "$options": "i" }, "delete_at": null } }
  ]
}

Usario: "¿quién es el {{rol}} de {{project_name}}?"
{
  "collection": "projects",
  "query_type": "aggregate",
  "query": [
    { "$match": { "name": { "$regex": "{{project_name}}", "$options": "i" } } },
    { "$unwind": "$assignedPersons" },
    { "$match": { "assignedPersons.rol": { "$regex": "{{rol}}", "$options": "i" } } },
    { "$replaceRoot": { "newRoot": "$assignedPersons" } }
  ],
  "example_texts": [
    "¿quién es el {{rol}} de {{project_name}}?",
    "mostrame al {{rol}} del proyecto {{project_name}}"
  ]
}


Usuario: "¿quién es el Scrum Master de Rubik?"
{
  "collection": "projects",
  "query_type": "aggregate",
  "query": [
    {
      "$match": {
        "name": { "$regex": "Rubik", "$options": "i" }
      }
    },
    {
      "$unwind": "$assignedPersons"
    },
    {
      "$match": {
        "assignedPersons.rol": { "$regex": "Scrum Master", "$options": "i" }
      }
    },
    {
      "$lookup": {
        "from": "collaborator",
        "let": { "proyId": "$_id", "rol": "$assignedPersons.rol" },
        "pipeline": [
          {
            "$match": {
              "$expr": {
                "$gt": [
                  {
                    "$size": {
                      "$filter": {
                        "input": { "$ifNull": ["$Proyectos", []] },
                        "as": "p",
                        "cond": {
                          "$and": [
                            { "$eq": ["$$p.projectId", "$$proyId"] },
                            {
                              "$regexMatch": {
                                "input": "$$p.rol",
                                "regex": "$$rol",
                                "options": "i"
                              }
                            }
                          ]
                        }
                      }
                    }
                  },
                  0
                ]
              }
            }
          }
        ],
        "as": "scrumMasterData"
      }
    },
    { "$unwind": "$scrumMasterData" },
    {
      "$replaceRoot": {
        "newRoot": "$scrumMasterData"
      }
    }
  ]
}

{
  "collection": "projects",
  "query_type": "aggregate",
  "query": [
    { "$match": { "name": { "$regex": "Rubik", "$options": "i" } } },
    { "$unwind": "$assignedPersons" },
    { "$match": { "assignedPersons.rol": { "$regex": "QA", "$options": "i" } } },
    {
      "$lookup": {
        "from": "collaborator",
        "let": { "proyId": "$_id", "rol": "$assignedPersons.rol" },
        "pipeline": [
          {
            "$match": {
              "$expr": {
                "$gt": [
                  {
                    "$size": {
                      "$filter": {
                        "input": { "$ifNull": ["$Proyectos", []] },
                        "as": "p",
                        "cond": {
                          "$and": [
                            { "$eq": ["$$p.projectId", "$$proyId"] },
                            {
                              "$regexMatch": {
                                "input": "$$p.rol",
                                "regex": "$$rol",
                                "options": "i"
                              }
                            }
                          ]
                        }
                      }
                    }
                  },
                  0
                ]
              }
            }
          }
        ],
        "as": "qaData"
      }
    },
    { "$unwind": "$qaData" },
    { "$replaceRoot": { "newRoot": "$qaData" } }
  ]
}



Usuario: "vacantes que requieran saber Angular"
{
  "collection": "vacancie",
  "query_type": "aggregate",
  "query": [
    {
      "$lookup": {
        "from": "technologies",
        "localField": "skills.technologyId",
        "foreignField": "_id",
        "as": "techInfo"
      }
    },
    {
      "$match": {
        "techInfo.name": { "$regex": "Angular", "$options": "i" },
        "delete_at": null
      }
    }
  ]
}
{
  "collection": "projects",
  "query_type": "aggregate",
  "query": [
    { "$match": { "name": { "$regex": "Rubik", "$options": "i" } } },
    { "$unwind": "$assignedPersons" },
    { "$match": { "assignedPersons.rol": { "$regex": "Project Manager", "$options": "i" } } },
    {
      "$lookup": {
        "from": "collaborator",
        "let": { "proyId": "$_id", "rol": "$assignedPersons.rol" },
        "pipeline": [
          {
            "$match": {
              "$expr": {
                "$gt": [
                  {
                    "$size": {
                      "$filter": {
                        "input": { "$ifNull": ["$Proyectos", []] },
                        "as": "p",
                        "cond": {
                          "$and": [
                            { "$eq": ["$$p.projectId", "$$proyId"] },
                            {
                              "$regexMatch": {
                                "input": "$$p.rol",
                                "regex": "$$rol",
                                "options": "i"
                              }
                            }
                          ]
                        }
                      }
                    }
                  },
                  0
                ]
              }
            }
          }
        ],
        "as": "pmData"
      }
    },
    { "$unwind": "$pmData" },
    { "$replaceRoot": { "newRoot": "$pmData" } }
  ]
}


Usuario: "proyectos con QAs que ingresaron en 2025"
{
  "collection": "projects",
  "query_type": "aggregate",
  "query": [
    { "$match": { "delete_at": null } },
    {
      "$lookup": {
        "from": "collaborator",
        "let": { "proyId": "$_id" },
        "pipeline": [
          { "$unwind": "$Proyectos" },
          { "$unwind": "$roles" },
          {
            "$match": {
              "$expr": {
                "$and": [
                  { "$eq": ["$Proyectos.projectId", "$$proyId"] },
                  { "$regexMatch": { "input": "$roles.rol", "regex": "QA", "options": "i" } },
                  {
                    "$and": [
                      { "$gte": ["$start_contrato", { "$toDate": "2025-01-01T00:00:00.000Z" }] },
                      { "$lt": ["$start_contrato", { "$toDate": "2026-01-01T00:00:00.000Z" }] }
                    ]
                  }
                ]
              }
            }
          }
        ],
        "as": "qaIngresaron2025"
      }
    },
    { "$match": { "qaIngresaron2025.0": { "$exists": true } } },
    {
      "$project": {
        "_id": 1,
        "name": 1,
        "client": 1,
        "category": 1,
        "managerName": 1,
        "qaIngresaron2025": {
          "first_name": 1,
          "last_name": 1,
          "start_contrato": 1,
          "roles": 1
        }
      }
    }
  ]
}

Usuario: "colaboradores cuyo contrato vence antes del 30/12/2025"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    {
      "$match": {
        "delete_at": null,
        "fin_contrato": { "$ne": null }
      }
    },
    {
      "$addFields": {
        "finContratoISO": { "$toDate": "$fin_contrato" }
      }
    },
    {
      "$match": {
        "$expr": {
          "$lt": [
            "$finContratoISO",
            {
              "$dateFromString": {
                "dateString": "2025-12-30T00:00:00.000Z"
              }
            }
          ]
        }
      }
    }
  ],
  "example_texts": [
    "colaboradores cuyo contrato vence antes del 30/12/2025",
    "contratos que vencen antes de fin de año",
    "personas con fecha de fin de contrato antes del 30-12-2025"
  ]
}




Usuario: "vacantes con skills en Python"
{
  "collection": "vacancie",
  "query_type": "aggregate",
  "query": [
    {
      "$lookup": {
        "from": "technologies",
        "localField": "skills.technologyId",
        "foreignField": "_id",
        "as": "techInfo"
      }
    },
    {
      "$match": {
        "techInfo.name": { "$regex": "Python", "$options": "i" },
        "delete_at": null
      }
    }
  ]
}

Usuario: "colaboradores que trabajan en proyectos con tecnología React"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    { "$unwind": "$Proyectos" },
    {
      "$lookup": {
        "from": "projects",
        "localField": "Proyectos.projectId",
        "foreignField": "_id",
        "as": "projectDetails"
      }
    },
    { "$unwind": "$projectDetails" },
    { "$unwind": "$projectDetails.assignedPersons" },
    {
      "$match": {
        "projectDetails.assignedPersons.tecnologias": { "$regex": "React", "$options": "i" },
        "delete_at": null
      }
    }
  ]
}

Usuario: "colaboradores asignados a proyectos activos (estado En ejecución)"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    { "$unwind": "$Proyectos" },
    {
      "$lookup": {
        "from": "projects",
        "localField": "Proyectos.projectId",
        "foreignField": "_id",
        "as": "projectData"
      }
    },
    { "$unwind": "$projectData" },
    {
      "$match": {
        "projectData.status": { "$regex": "En ejecución", "$options": "i" },
        "delete_at": null
      }
    }
  ]
}

Usuario: "proyectos con colaboradores senior y tecnología Java"
{
  "collection": "projects",
  "query_type": "aggregate",
  "query": [
    { "$unwind": "$assignedPersons" },
    {
      "$match": {
        "assignedPersons.seniority": { "$regex": "Senior", "$options": "i" },
        "assignedPersons.tecnologias": { "$regex": "Java", "$options": "i" },
        "delete_at": null
      }
    }
  ]
}

Usuario: "colaboradores que usan más de 3 tecnologías"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    {
      "$addFields": {
        "techCount": { "$size": { "$ifNull": ["$tecnologias", []] } }
      }
    },
    { "$match": { "techCount": { "$gt": 3 }, "delete_at": null } }
  ]
}

Usuario : Colaboradores Semisenior con proyectos asignados
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    { "$unwind": "$roles" },
    {
      "$match": {
        "roles.seniority": { "$regex": "semisenior", "$options": "i" },
        "delete_at": null
      }
    },
    {
      "$match": {
        "$expr": {
          "$gt": [
            { "$size": { "$ifNull": ["$Proyectos", []] } },
            0
          ]
        }
      }
    }
  ]
}
Usuario: "mostrar QA disponibles"
Usuario: "DevOps libres"
Usuario: "quiénes son los diseñadores disponibles"
Usuario: "alguien de backend sin asignar completamente"
Usuario: "colaboradores sin carga total con rol QA"
Usuario: "colaborador disponible para frontend"
Usuario: "hay PO disponibles"
{
  "collection": "collaborator",
  "query_type": "aggregate",
  "query": [
    {
      "$match": {
        "delete_at": null
      }
    },
    {
      "$lookup": {
        "from": "jornadas",
        "localField": "jornadaId",
        "foreignField": "_id",
        "as": "jornadaInfo"
      }
    },
    { "$unwind": "$jornadaInfo" },
    {
      "$addFields": {
        "totalHorasAsignadas": {
          "$sum": {
            "$map": {
              "input": { "$ifNull": ["$Proyectos", []] },
              "as": "p",
              "in": "$$p.horasAsignadas"
            }
          }
        }
      }
    },
    {
      "$addFields": {
        "rolPrincipal": {
          "$arrayElemAt": ["$roles.rol", 0]
        }
      }
    },
    {
      "$match": {
        "rolPrincipal": { "$regex": "QA", "$options": "i" }, // ← reemplazar QA por DevOps, UX, etc según la intención
        "$expr": {
          "$lt": ["$totalHorasAsignadas", "$jornadaInfo.hours"]
        }
      }
    }
  ]
}



Usuario:Proyectos con más colaboradores asignados
{
  "collection": "projects",
  "query_type": "aggregate",
  "query": [
    {
      "$addFields": {
        "colaboradoresAsignados": {
          "$size": { "$ifNull": ["$assignedPersons", []] }
        }
      }
    },
    { "$sort": { "colaboradoresAsignados": -1 } },
    { "$limit": 10 }
  ]
}
Usuario:Proyectos con colaboradores QAs que ingresaron en 2025
{
  "collection": "projects",
  "query_type": "find",
  "query": {
    "assignedPersons": {
      "$elemMatch": {
        "rol": { "$regex": "QA", "$options": "i" },
        "startDate": {
          "$gte": "2025-01-01T00:00:00.000Z",
          "$lt": "2026-01-01T00:00:00.000Z"
        }
      }
    },
    "delete_at": null
  }
}

Mejora final: fallback si no entiende la intención
{
  "error": "No he podido entender tu solicitud."
}

"""

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_entities(user_query: str) -> dict | None:

    try:

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": INTENT_EXTRACTION_PROMPT},
                {"role": "user", "content": user_query},
            ],
            response_format={"type": "json_object"},
        )

        json_string = response.choices[0].message.content
        print(f"STRING RECIBIDO: {json_string}")

        data = json.loads(json_string)
        print(f"JSON PARSEADO CON ÉXITO: {data}")

        print("--- Devolviendo resultado exitoso. ---")
        return data

    except Exception as e:

        print("!!!!!!!!!! ERROR DENTRO DE extract_entities !!!!!!!!!!")
        print(f"Se produjo una excepción: {type(e).__name__}: {e}")
        print("--- Devolviendo None debido a un error. ---")
        return None
