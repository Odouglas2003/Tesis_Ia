from typing import Dict, List


def build_assignment_status_pipeline(status: str, base_filter: Dict) -> List[Dict]:
    """Construye un pipeline de agregación para filtrar colaboradores basado en su estado de asignación
    de proyectos."""
    pipeline = [{"$match": base_filter}] if base_filter else []
    pipeline.extend(
        [
            {
                "$addFields": {
                    "totalHorasAsignadasEnProyectos": {
                        "$ifNull": [{"$sum": "$Proyectos.horasAsignadas"}, 0]
                    },
                    "jornada_obj_id": {
                        "$cond": {
                            "if": {
                                "$and": [
                                    {"$ne": ["$jornadaId", None]},
                                    {"$ne": ["$jornadaId", ""]},
                                ]
                            },
                            "then": {"$toObjectId": "$jornadaId"},
                            "else": None,
                        }
                    },
                }
            },
            {
                "$lookup": {
                    "from": "jornadas",
                    "localField": "jornada_obj_id",
                    "foreignField": "_id",
                    "as": "jornada_details",
                }
            },
            {
                "$unwind": {
                    "path": "$jornada_details",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$addFields": {
                    "horasJornadaMensual": {
                        "$ifNull": [{"$toInt": "$jornada_details.hours"}, 160]
                    }
                }
            },
        ]
    )
    if status == "sin_asignacion":
        pipeline.append({"$match": {"totalHorasAsignadasEnProyectos": 0}})
    elif status == "subasignado":
        pipeline.append(
            {
                "$match": {
                    "$expr": {
                        "$lt": [
                            "$totalHorasAsignadasEnProyectos",
                            "$horasJornadaMensual",
                        ]
                    }
                }
            }
        )
        pipeline.append({"$match": {"totalHorasAsignadasEnProyectos": {"$gt": 0}}})
    elif status == "asignado":
        pipeline.append(
            {
                "$match": {
                    "$expr": {
                        "$eq": [
                            "$totalHorasAsignadasEnProyectos",
                            "$horasJornadaMensual",
                        ]
                    }
                }
            }
        )
    elif status == "sobreasignado":
        pipeline.append(
            {
                "$match": {
                    "$expr": {
                        "$gt": [
                            "$totalHorasAsignadasEnProyectos",
                            "$horasJornadaMensual",
                        ]
                    }
                }
            }
        )
    pipeline.append(
        {
            "$project": {
                "jornada_details": 0,
                "horasJornadaMensual": 0,
                "jornada_obj_id": 0,
                "totalHorasAsignadasEnProyectos": 0,
            }
        }
    )
    return pipeline


def build_projects_by_collab_properties_pipeline(
    collab_filters: List[Dict],
) -> List[Dict]:
    """Filtra proyectos basado en las propiedades de los colaboradores asignados."""
    match_pipeline = []
    if collab_filters:
        match_pipeline.append({"$match": {"$and": collab_filters}})

    match_pipeline.append(
        {"$match": {"$expr": {"$in": [{"$toString": "$_id"}, "$$assigned_ids_str"]}}}
    )

    return [
        {
            "$lookup": {
                "from": "collaborator",
                "let": {"assigned_ids_str": {"$ifNull": ["$assignedPersons.id", []]}},
                "pipeline": match_pipeline,
                "as": "matching_collaborators",
            }
        },
        {"$match": {"matching_collaborators": {"$ne": []}}},
        {"$project": {"matching_collaborators": 0}},
    ]


def build_collabs_by_jornada_pipeline(jornada_name: str) -> List[Dict]:

    return [
        {
            "$lookup": {
                "from": "jornadas",
                "let": {"jornada_id": {"$toObjectId": "$jornadaId"}},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {"$eq": ["$_id", "$$jornada_id"]},
                            "name": {"$regex": jornada_name, "$options": "i"},
                        }
                    }
                ],
                "as": "jornada_details",
            }
        },
        {"$match": {"jornada_details": {"$ne": []}}},
        {"$project": {"jornada_details": 0}},
    ]


def build_availability_pipeline(base_filter: Dict) -> List[Dict]:

    pipeline = [{"$match": base_filter}] if base_filter else []
    pipeline.extend(
        [
            {
                "$addFields": {
                    "totalHorasAsignadasEnProyectos": {
                        "$ifNull": [{"$sum": "$Proyectos.horasAsignadas"}, 0]
                    }
                }
            },
            {
                "$lookup": {
                    "from": "jornadas",
                    "localField": "jornadaId",
                    "foreignField": "_id",
                    "as": "jornada_details",
                }
            },
            {
                "$unwind": {
                    "path": "$jornada_details",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$addFields": {
                    "horasJornadaMensual": {
                        "$ifNull": [{"$toInt": "$jornada_details.hours"}, 160]
                    }
                }
            },
            {
                "$match": {
                    "$expr": {
                        "$lt": [
                            "$totalHorasAsignadasEnProyectos",
                            "$horasJornadaMensual",
                        ]
                    }
                }
            },
            {"$project": {"jornada_details": 0, "horasJornadaMensual": 0}},
        ]
    )
    return pipeline


def build_multi_project_pipeline() -> List[Dict]:

    return [
        {"$match": {"Proyectos": {"$exists": True, "$ne": None}}},
        {"$addFields": {"project_count": {"$size": "$Proyectos"}}},
        {"$match": {"project_count": {"$gt": 1}}},
        {"$project": {"project_count": 0}},
    ]


def build_collabs_by_project_pipeline(project_name: str) -> List[Dict]:

    return [
        {"$match": {"name": {"$regex": project_name, "$options": "i"}}},
        {"$limit": 1},
        {"$unwind": "$assignedPersons"},
        {
            "$lookup": {
                "from": "collaborator",
                "let": {"person_id": {"$toObjectId": "$assignedPersons.id"}},
                "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$person_id"]}}}],
                "as": "collab_details",
            }
        },
        {"$unwind": "$collab_details"},
        {"$replaceRoot": {"newRoot": "$collab_details"}},
    ]


def build_mongo_query_from_entities(entities: Dict) -> Dict:
    project_filters = []
    collab_filters = []
    mongo_filter_parts = []

    collection = entities.get("collection")
    filters = entities.get("filters", [])

    field_map = {
        "nombre_colaborador": "first_name",
        "last_name": "last_name",
        "rol": "roles.rol",
        "seniority": "roles.seniority",
        "tecnologia": "tecnologias",
        "fecha_ingreso": "start_contrato",
        "modalidad": "jornadaId",
        "fecha_fin_contrato": "fin_contrato",
        "cliente": "client",
        "manager": "managerName",
        "estado_proyecto": "status",
        "categoria_proyecto": "category",
        "fecha_inicio_proyecto": "startDate",
        "fecha_fin_proyecto": "endDate",
        "rol_asignado_proyecto": "assignedPersons.rol",
        "rol_vacante": "vacancieName",
        "seniority_vacante": "seniority",
        "tecnologia_vacante": "tecnologias",
        "manager_vacante": "manager_name",
        "proyecto_vacante": "projectId.name",
        "fecha_pedido_vacante": "orderDate",
        "fecha_inicio_vacante": "startDate",
        "estado_vacante": "status",
        "vacante_horas_requeridas": "time",
        "tecnologia_proyecto": "assignedPersons.tecnologias",
    }

    for f in filters:
        field = f.get("field")
        value = f.get("value")

        if field == "estado_asignacion":
            other_filters = []
            for other_f in filters:
                if other_f.get("field") != "estado_asignacion":
                    db_field = field_map.get(other_f.get("field"))
                    if db_field:
                        other_filters.append(
                            {
                                db_field: {
                                    "$regex": other_f.get("value"),
                                    "$options": "i",
                                }
                            }
                        )
            base_filter = {"$and": other_filters} if other_filters else {}
            return {
                "collection": "collaborator",
                "pipeline": build_assignment_status_pipeline(value, base_filter),
            }
        if field == "modalidad":
            return {
                "collection": "collaborator",
                "pipeline": build_collabs_by_jornada_pipeline(value),
            }
        if field == "disponibilidad":
            base_filter = {"$and": mongo_filter_parts} if mongo_filter_parts else {}
            return {
                "collection": "collaborator",
                "pipeline": build_availability_pipeline(base_filter),
            }
        if field == "asignacion_proyectos":
            return {
                "collection": "collaborator",
                "pipeline": build_multi_project_pipeline(),
            }
        if field == "nombre_proyecto":
            return {
                "collection": "projects",
                "pipeline": build_collabs_by_project_pipeline(value),
            }

    collab_centric_fields = ["rol", "seniority", "tecnologia", "fecha_ingreso"]
    is_project_query_with_collab_filter = collection == "projects" and any(
        f.get("field") in collab_centric_fields for f in filters
    )

    if is_project_query_with_collab_filter:
        for f in filters:
            field, op, value = f.get("field"), f.get("operator"), f.get("value")
            db_field = field_map.get(field)
            if field in collab_centric_fields and db_field:
                if op == "year":
                    collab_filters.append(
                        {
                            "$expr": {
                                "$eq": [{"$year": {"$toDate": f"${db_field}"}}, value]
                            }
                        }
                    )
                else:
                    collab_filters.append(
                        {db_field: {"$regex": value, "$options": "i"}}
                    )
            elif db_field:
                project_filters.append({db_field: {"$regex": value, "$options": "i"}})

        pipeline = build_projects_by_collab_properties_pipeline(collab_filters)
        if project_filters:
            pipeline.insert(0, {"$match": {"$and": project_filters}})

        return {"collection": "projects", "pipeline": pipeline}
    else:
        for f in filters:
            field, op, value = f.get("field"), f.get("operator"), f.get("value")
            db_field = field_map.get(field.lower())
            if not db_field:
                print(
                    f"ADVERTENCIA: Campo conceptual '{field}' no reconocido. Ignorando filtro."
                )
                continue

            if op == "eq":
                mongo_filter_parts.append(
                    {db_field: {"$regex": f"^{value}$", "$options": "i"}}
                )
            elif op == "regex":
                mongo_filter_parts.append(
                    {db_field: {"$regex": value, "$options": "i"}}
                )
            elif op == "year":
                mongo_filter_parts.append(
                    {"$expr": {"$eq": [{"$year": {"$toDate": f"${db_field}"}}, value]}}
                )
            elif op == "month":
                mongo_filter_parts.append(
                    {"$expr": {"$eq": [{"$month": {"$toDate": f"${db_field}"}}, value]}}
                )

        final_filter = {}
        if mongo_filter_parts:
            if len(mongo_filter_parts) > 1:
                final_filter["$and"] = mongo_filter_parts
            else:
                final_filter = mongo_filter_parts[0]

        return {"collection": collection, "filter": final_filter}
