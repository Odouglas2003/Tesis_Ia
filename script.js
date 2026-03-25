document.addEventListener('DOMContentLoaded', () => {
    const jsonRequestTextarea = document.getElementById('jsonRequest');
    const sendRequestBtn = document.getElementById('sendRequestBtn');
    const loadingDiv = document.getElementById('loading');
    const errorArea = document.getElementById('errorArea');
    
    const resultsArea = document.getElementById('resultsArea');
    const overallStatusMessageDiv = document.getElementById('overallStatusMessage');
    const proposalsByRoleContainer = document.getElementById('proposalsByRoleContainer');
    const finalActionsContainer = document.getElementById('finalActionsContainer');
    const saveSelectionButton = document.getElementById('saveSelectionButton');
    
    const finalTeamArea = document.getElementById('finalTeamArea');
    const finalTeamList = document.getElementById('finalTeamList');
    const finalVacancyMessagesDiv = document.getElementById('finalVacancyMessages');
    const startNewProposalButton = document.getElementById('startNewProposalButton');

    const API_ENDPOINT = 'http://127.0.0.1:8000/api/teams/generate_proposal';

    let currentApiResponse = null; // Almacena la respuesta completa de la API
    let selectedCandidates = {}; // { "roleName_plazaIndex": candidateId }
    let originalRolesRequested = []; // Almacena { name: "roleName", quantity: X }

    // Pre-llenar con el JSON de ejemplo
    const exampleRequest = { /* ... (Copia tu JSON de ejemplo de Postman aquí) ... */ 
        "project_name": "Plataforma E-learning Interactiva con IA V2",
        "project_description": "Desarrollo de una nueva plataforma de e-learning que utilizará React y TypeScript para el frontend, y Python con FastAPI para el backend. La base de datos será MongoDB. Se incorporarán elementos de IA para recomendaciones personalizadas de cursos, posiblemente usando Langchain y OpenAI. El despliegue se realizará en la nube, preferiblemente AWS, utilizando Docker y Kubernetes para la orquestación. Se requieren pruebas exhaustivas con Selenium y gestión de proyecto con Jira.",
        "roles_requested": [
            {"role_name": "Backend Developer","quantity": 1,"required_technologies": ["Python", "FastAPI", "MongoDB"],"max_carga_horaria_deseada": 40},
            {"role_name": "Frontend Developer","quantity": 1,"required_technologies": ["React", "TypeScript"],"max_carga_horaria_deseada": 40},
            {"role_name": "QA Engineer","quantity": 1,"required_technologies": ["Selenium"],"max_carga_horaria_deseada": 30}
        ]
    };
    jsonRequestTextarea.value = JSON.stringify(exampleRequest, null, 2);

    sendRequestBtn.addEventListener('click', async () => {
        const requestJsonString = jsonRequestTextarea.value;
        let requestBody;

        loadingDiv.style.display = 'block';
        errorArea.style.display = 'none'; errorArea.textContent = '';
        resultsArea.style.display = 'none'; finalTeamArea.style.display = 'none';
        proposalsByRoleContainer.innerHTML = '';
        overallStatusMessageDiv.textContent = '';
        finalActionsContainer.style.display = 'none';
        saveSelectionButton.disabled = true;
        currentApiResponse = null; selectedCandidates = {}; originalRequestedRoles = [];

        try {
            requestBody = JSON.parse(requestJsonString);
        } catch (parseErr) {
            errorArea.textContent = `Error en JSON de solicitud: ${parseErr.message}`;
            errorArea.style.display = 'block'; loadingDiv.style.display = 'none'; sendRequestBtn.disabled = false;
            return;
        }
        
        originalRequestedRoles = requestBody.roles_requested.map(r => ({ name: r.role_name, quantity: r.quantity }));
        console.log("Enviando al backend:", requestBody);

        try {
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            const responseData = await response.json(); // Asumimos que el backend siempre devuelve JSON
            console.log("Respuesta del backend:", responseData);

            if (!response.ok) {
                throw new Error(responseData.detail || responseData.message || `Error del servidor: ${response.status}`);
            }
            currentApiResponse = responseData;
            renderProposals(responseData);
            updateSaveButtonState();

        } catch (err) {
            console.error("Error en fetch o parseo:", err);
            errorArea.textContent = `Error API: ${err.message}`;
            errorArea.style.display = 'block';
        } finally {
            loadingDiv.style.display = 'none';
            sendRequestBtn.disabled = false;
        }
    });

    function renderProposals(data) {
        resultsArea.style.display = 'block';
        proposalsByRoleContainer.innerHTML = ''; 

        overallStatusMessageDiv.textContent = `Estado General: ${data.overall_status_message || 'N/A'}`;
        overallStatusMessageDiv.className = `status-message ${getMsgClass(data.overall_status_message, true)}`;

        if (data.proposals_by_role && data.proposals_by_role.length > 0) {
            finalActionsContainer.style.display = 'block';
            data.proposals_by_role.forEach(roleGroup => {
                const roleGroupEl = document.createElement('div');
                roleGroupEl.classList.add('role-proposal-group');
                
                let headerHtml = `<h3>${roleGroup.role_name_requested} (Plazas: ${roleGroup.quantity_requested})</h3>`;
                headerHtml += `<p class="status-message ${getMsgClass(roleGroup.status_message)}">${roleGroup.status_message || 'Sin estado específico.'}</p>`;
                roleGroupEl.innerHTML = headerHtml;

                for (let i = 0; i < roleGroup.quantity_requested; i++) { // Iterar por cada plaza solicitada
                    const plazaDiv = document.createElement('div');
                    plazaDiv.innerHTML = `<h4>Opciones para Plaza #${i + 1}:</h4>`;
                    const radioGroupName = `candidate_for_${roleGroup.role_name_requested.replace(/\s+/g, '_')}_plaza_${i}`;
                    
                    if (roleGroup.candidates_proposed && roleGroup.candidates_proposed.length > 0) {
                        // Ofrecer todos los candidatos propuestos como opción para esta plaza
                        // Idealmente, si hay múltiples plazas, se querría una lógica más compleja
                        // para no proponer el mismo candidato dos veces, pero para visualización está bien.
                        roleGroup.candidates_proposed.forEach(candidate => {
                            const card = createCandidateCard(candidate, radioGroupName, `${roleGroup.role_name_requested}_${i}`);
                            plazaDiv.appendChild(card);
                        });
                    } else {
                        plazaDiv.innerHTML += `<p>No hay candidatos propuestos para esta plaza.</p>`;
                    }
                    roleGroupEl.appendChild(plazaDiv);
                }
                proposalsByRoleContainer.appendChild(roleGroupEl);
            });
        }
    }

    function createCandidateCard(candidate, radioGroupName, checkpointKeyBase) {
        const card = document.createElement('div');
        card.classList.add('candidate-card');
        const radioId = `cand_${checkpointKeyBase}_${candidate.id}`; // checkpointKeyBase ya incluye el índice de la plaza

        if (selectedCandidates[checkpointKeyBase] === candidate.id) {
            card.classList.add('selected-candidate-card');
        }

        let cargaHorariaInfo = `${candidate.carga_horaria_actual}hs`;
        if (candidate.carga_horaria_actual >= 160) {
            cargaHorariaInfo = `<span style="color:red; font-weight:bold;">${candidate.carga_horaria_actual}hs (EXCESIVA)</span>`;
        } else if (candidate.carga_horaria_actual >= 100) {
            cargaHorariaInfo = `<span style="color:orange;">${candidate.carga_horaria_actual}hs (Alta)</span>`;
        }
        
        card.innerHTML = `
            <input type="radio" name="${radioGroupName}" id="${radioId}" value="${candidate.id}" 
                   ${selectedCandidates[checkpointKeyBase] === candidate.id ? 'checked' : ''}>
            <label for="${radioId}">
                <strong>${candidate.nombre_completo || 'Nombre N/A'}</strong> (ID: ${candidate.id})<br>
                <span class="details">Email: ${candidate.email || 'N/A'}</span>
                <span class="details">Puesto Asignado: ${candidate.puesto_asignado_interno || 'N/A'}</span>
                <span class="details">Seniority (Original): ${candidate.seniority_original_csv || 'N/A'}</span>
                <span class="details">Carga Horaria: ${cargaHorariaInfo}</span>
                <span class="details">Disp. hasta: ${candidate.fecha_salida_str_csv || 'N/A'}</span>
                <span class="details">Score: ${candidate.score_calculado !== undefined ? candidate.score_calculado.toFixed(3) : 'N/A'}</span>
            </label>
        `;
        card.querySelector('input[type="radio"]').addEventListener('change', (e) => {
            handleCandidateSelection(checkpointKeyBase, parseInt(e.target.value), radioGroupName);
        });
        return card;
    }
    
    function handleCandidateSelection(checkpointKey, candidateId, radioGroupName) {
        selectedCandidates[checkpointKey] = candidateId;
        // Actualizar UI para reflejar selección
        document.querySelectorAll(`input[name="${radioGroupName}"]`).forEach(radio => {
            radio.closest('.candidate-card').classList.remove('selected-candidate-card');
        });
        const selectedRadio = document.getElementById(`cand_${checkpointKey.replace(/ /g, '_')}_${candidateId}`); // Asegurar que el ID sea correcto
        if (selectedRadio) {
            selectedRadio.closest('.candidate-card').classList.add('selected-candidate-card');
        }
        console.log("Selección Actualizada:", selectedCandidates);
        updateSaveButtonState();
    }

    function updateSaveButtonState() {
        let allSlotsFilled = true;
        if (originalRequestedRoles.length === 0) {
            allSlotsFilled = false;
        }
        originalRequestedRoles.forEach(role => {
            for (let i = 0; i < role.quantity; i++) {
                const key = `${role.name}_${i}`;
                if (!selectedCandidates[key]) {
                    allSlotsFilled = false;
                    break;
                }
            }
            if (!allSlotsFilled) return;
        });
        saveSelectionButton.disabled = !allSlotsFilled;
    }

    function getMsgClass(message = "", isOverall = false) {
        const lowerMsg = message.toLowerCase();
        if (lowerMsg.includes("error") || lowerMsg.includes("vacante sugerida")) return 'status-error';
        if (lowerMsg.includes("advertencia") || lowerMsg.includes("observaciones")) return 'status-warning';
        if (lowerMsg.includes("propuestos") || lowerMsg.includes("propuestas generadas exitosamente")) return isOverall ? 'status-ok' : '';
        return '';
    }

    saveSelectionButton.addEventListener('click', () => {
        finalTeamList.innerHTML = '';
        finalVacancyMessagesDiv.innerHTML = '';
        let assembledTeam = [];
        let vacancyMessagesGenerated = [];
        let uniqueVacancyReasons = new Set(); // Para no repetir mensajes de vacante genéricos

        console.log("Definiendo equipo con selecciones:", selectedCandidates);
        console.log("Roles originalmente solicitados:", originalRequestedRoles);
        console.log("Datos de la API propuestos:", currentApiResponse);


        if (!currentApiResponse || !currentApiResponse.proposals_by_role) {
            finalVacancyMessagesDiv.innerHTML = "<p>Error: No hay datos de propuestas de la API para procesar.</p>";
            finalTeamArea.style.display = 'block';
            resultsArea.style.display = 'none';
            return;
        }
        
        originalRequestedRoles.forEach(reqRole => {
            for (let i = 0; i < reqRole.quantity; i++) { // Por cada plaza del rol
                const checkpointKey = `${reqRole.name}_${i}`;
                const selectedCandidateId = selectedCandidates[checkpointKey];
                const roleProposalGroup = currentApiResponse.proposals_by_role.find(p => p.role_name_requested === reqRole.name);
                let candidateSelectedForThisSlot = false;

                if (selectedCandidateId && roleProposalGroup && roleProposalGroup.candidates_proposed) {
                    const candidate = roleProposalGroup.candidates_proposed.find(c => c.id === selectedCandidateId);
                    if (candidate) {
                        assembledTeam.push(candidate);
                        const li = document.createElement('li');
                        li.textContent = `${candidate.nombre_completo} (${candidate.puesto_asignado_interno || 'N/A'}) - Rol Solicitado: ${reqRole.name} (Plaza ${i+1}) - Carga: ${candidate.carga_horaria_actual}hs`;
                        
                        let cargaWarning = "";
                        if (candidate.carga_horaria_actual >= 160) cargaWarning = ` (¡EXCESIVA!)`;
                        else if (candidate.carga_horaria_actual >= 100) cargaWarning = ` (Alta)`;
                        else if (candidate.carga_horaria_actual > (reqRole.max_carga_horaria_deseada || Config.MAX_CARGA_HORARIA_DESEADA_DEFAULT)) cargaWarning = ` (Supera deseada)`;
                        
                        if(cargaWarning) li.innerHTML += ` <strong style="color: ${cargaWarning.includes('EXCESIVA') ? 'red' : 'orange'};">${cargaWarning}</strong>`;
                        
                        finalTeamList.appendChild(li);
                        candidateSelectedForThisSlot = true;
                    }
                }

                if (!candidateSelectedForThisSlot) {
                    uniqueVacancyReasons.add(`VACANTE: No se seleccionó/encontró candidato para ${reqRole.name} (Plaza #${i + 1}).`);
                }
            }
            // Chequear mensaje de status del backend para este rol
            const roleProposal = currentApiResponse.proposals_by_role.find(p => p.role_name_requested === reqRole.name);
            if (roleProposal && roleProposal.status_message && roleProposal.status_message.toLowerCase().includes("vacante")) {
                uniqueVacancyReasons.add(`Backend sugiere para ${reqRole.name}: ${roleProposal.status_message}`);
            }
        });
        
        uniqueVacancyReasons.forEach(reason => {
            const p = document.createElement('p');
            p.innerHTML = reason.startsWith("VACANTE:") ? `<strong class="vacancy-note">${reason}</strong>` : `<span class="warning-note">${reason}</span>`;
            finalVacancyMessagesDiv.appendChild(p);
        });

        if (uniqueVacancyReasons.size > 0 && !document.getElementById('genericVacancyButton')) {
            const vacancyButton = document.createElement('button');
            vacancyButton.id = 'genericVacancyButton';
            vacancyButton.textContent = 'Gestionar Vacantes / Ver Observaciones';
            vacancyButton.classList.add('generate-vacancy-final');
            vacancyButton.addEventListener('click', () => {
                alert('FUNCIONALIDAD PENDIENTE: Aquí se mostrarían detalles de vacantes y se gestionaría su creación/seguimiento.');
            });
            finalVacancyMessagesDiv.insertBefore(vacancyButton, finalVacancyMessagesDiv.firstChild);
        }

        finalTeamArea.style.display = 'block';
        resultsArea.style.display = 'none';
        finalActionsContainer.style.display = 'none';
    });

    startNewProposalButton.addEventListener('click', () => {
        jsonRequestTextarea.value = JSON.stringify(exampleRequest, null, 2); // Reset con ejemplo
        finalTeamArea.style.display = 'none';
        resultsArea.style.display = 'none';
        errorArea.style.display = 'none'; errorArea.textContent = '';
        currentApiResponse = null; selectedCandidates = {}; originalRequestedRoles = [];
        saveSelectionButton.disabled = true;
    });

    // Configuración simulada en el frontend para parámetros visuales o umbrales.
    // Idealmente, si son importantes y configurables, vendrían de un endpoint de config del backend.
    window.Config = {
        MAX_CANDIDATES_PER_ROLE: 3, // Cuántas opciones mostrar por plaza
        CARGA_HORARIA_MAX_RECOMENDADA: 80 // Umbral para advertencia visual, no necesariamente el mismo que max_carga_horaria_deseada
    };

}); // Fin DOMContentLoaded