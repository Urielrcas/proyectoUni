document.addEventListener('DOMContentLoaded', function() {
    // --- Referencias a elementos del DOM ---
    const noteCreationBox = document.querySelector('.note-creation-box');
    const titleInput = noteCreationBox.querySelector('.note-title-input');
    const contentTextarea = noteCreationBox.querySelector('.note-content-textarea');
    const reminderSection = noteCreationBox.querySelector('.reminder-section'); 
    const saveButton = noteCreationBox.querySelector('button[type="submit"]');

    // Inputs de fecha y hora del recordatorio
    const reminderDateInput = document.getElementById('reminder_date');
    const reminderTimeInput = document.getElementById('reminder_time');

    // --- Funciones para expandir y colapsar la caja de creación ---
    function expandBox() {
        if (!noteCreationBox.classList.contains('expanded')) {
            noteCreationBox.classList.add('expanded');
            contentTextarea.style.height = '60px'; 
            contentTextarea.style.padding = '8px 0';
            contentTextarea.style.marginBottom = '15px';
            contentTextarea.style.opacity = '1';
            contentTextarea.style.visibility = 'visible';

            reminderSection.style.height = 'auto';
            reminderSection.style.padding = '8px 0';
            reminderSection.style.opacity = '1';
            reminderSection.style.visibility = 'visible';

            saveButton.style.display = 'block'; 
        }
    }

    function collapseBox() {
        if (!titleInput.value.trim() && !contentTextarea.value.trim() && 
            !reminderDateInput.value && !reminderTimeInput.value) {
            noteCreationBox.classList.remove('expanded');
            contentTextarea.style.height = '0';
            contentTextarea.style.padding = '0';
            contentTextarea.style.marginBottom = '0';
            contentTextarea.style.opacity = '0';
            contentTextarea.style.visibility = 'hidden';

            reminderSection.style.height = '0';
            reminderSection.style.padding = '0';
            reminderSection.style.opacity = '0';
            reminderSection.style.visibility = 'hidden';

            saveButton.style.display = 'none'; 
        }
    }

    // --- Event Listeners para expansión y colapso ---
    titleInput.addEventListener('focus', expandBox); 
    contentTextarea.addEventListener('focus', expandBox);
    if (reminderDateInput) reminderDateInput.addEventListener('focus', expandBox);
    if (reminderTimeInput) reminderTimeInput.addEventListener('focus', expandBox);

    noteCreationBox.addEventListener('click', function(event) {
        if (event.target !== saveButton) { 
            expandBox();
        }
    });

    document.addEventListener('click', function(event) {
        if (!noteCreationBox.contains(event.target)) {
            collapseBox();
        }
    });

    // Mostrar u ocultar botón guardar según contenido
    function updateSaveButtonVisibility() {
        if (titleInput.value.trim() !== '' || contentTextarea.value.trim() !== '' || 
            reminderDateInput.value !== '' || reminderTimeInput.value !== '') {
            saveButton.style.display = 'block';
        } else {
            saveButton.style.display = 'none';
        }
    }
    titleInput.addEventListener('input', updateSaveButtonVisibility);
    contentTextarea.addEventListener('input', updateSaveButtonVisibility);
    if (reminderDateInput) reminderDateInput.addEventListener('change', updateSaveButtonVisibility); 
    if (reminderTimeInput) reminderTimeInput.addEventListener('change', updateSaveButtonVisibility); 
    updateSaveButtonVisibility();

    // --- Lógica de recordatorios (Alarma) ---
    const alarmSound = new Audio('https://www.soundjay.com/buttons/beep-07.wav'); 

    let triggeredAlarms = new Set();
    try {
        const storedAlarms = localStorage.getItem('triggeredAlarms');
        if (storedAlarms) {
            triggeredAlarms = new Set(JSON.parse(storedAlarms));
        }
    } catch (e) {
        console.error("Error al cargar alarmas de localStorage:", e);
        triggeredAlarms = new Set();
    }

    function saveTriggeredAlarms() {
        try {
            localStorage.setItem('triggeredAlarms', JSON.stringify(Array.from(triggeredAlarms)));
        } catch (e) {
            console.error("Error al guardar alarmas en localStorage:", e);
        }
    }

    function checkReminders() {
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = String(now.getMonth() + 1).padStart(2, '0');
        const currentDay = String(now.getDate()).padStart(2, '0');
        const currentDateString = `${currentYear}-${currentMonth}-${currentDay}`;

        document.querySelectorAll('.note-card').forEach(card => {
            const taskId = card.dataset.taskId;
            const reminderDate = card.dataset.reminderDate;
            const reminderTime = card.dataset.reminderTime;
            const taskTitle = card.querySelector('h3').textContent;

            if (!reminderDate && !reminderTime) return;

            let reminderDateTime = null;
            if (reminderDate && reminderTime) {
                reminderDateTime = new Date(`${reminderDate}T${reminderTime}:00`);
            } else if (reminderDate) {
                reminderDateTime = new Date(`${reminderDate}T00:00:00`);
            } else if (reminderTime) {
                reminderDateTime = new Date(`${currentDateString}T${reminderTime}:00`);
                if (reminderDateTime < now) {
                    reminderDateTime.setDate(reminderDateTime.getDate() + 1);
                }
            }

            if (!reminderDateTime) return;

            // --- RESET ALARMA SI FECHA/HORA CAMBIÓ ---
            const key = `alarm_${taskId}`;
            const lastReminderTimeStr = localStorage.getItem(key);
            const currentReminderTimeStr = reminderDateTime.toISOString();

            if (lastReminderTimeStr !== currentReminderTimeStr) {
                // Fecha/hora cambiada, resetear alarma
                triggeredAlarms.delete(taskId);
                localStorage.removeItem(`triggered_${taskId}`);
                localStorage.setItem(key, currentReminderTimeStr);
            }

            if (triggeredAlarms.has(taskId)) return;

            const thresholdFuture = new Date(now.getTime() + 10 * 1000);
            const thresholdPast = new Date(now.getTime() - 10 * 1000);

            if (reminderDateTime >= thresholdPast && reminderDateTime <= thresholdFuture) {
                alarmSound.play();
                alert(`¡Recordatorio para "${taskTitle}"!\nFecha: ${reminderDate || 'Hoy'}\nHora: ${reminderTime || 'Todo el día'}`);
                triggeredAlarms.add(taskId);
                saveTriggeredAlarms();
                localStorage.setItem(`triggered_${taskId}`, "1");
            } else if (reminderDateTime < thresholdPast) {
                triggeredAlarms.add(taskId);
                saveTriggeredAlarms();
                localStorage.setItem(`triggered_${taskId}`, "1");
            }
        });
    }

    setInterval(checkReminders, 5000);
    checkReminders();
});

document.addEventListener('DOMContentLoaded', function () {
    const noteBox = document.querySelector('.note-creation-box');
    const titleInput = noteBox.querySelector('.note-title-input');
    const contentTextarea = noteBox.querySelector('.note-content-textarea');

    noteBox.addEventListener('click', function () {
        noteBox.classList.add('expanded');
        contentTextarea.style.display = 'block';
    });

    document.addEventListener('click', function (event) {
        if (!noteBox.contains(event.target)) {
            noteBox.classList.remove('expanded');
            contentTextarea.style.display = 'none';
            titleInput.value = '';
            contentTextarea.value = '';
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const alertas = document.querySelectorAll('.alerta');
    if(alertas.length > 0){
        const alarmSound = new Audio('https://www.soundjay.com/buttons/beep-07.wav'); 
        alarmSound.play();

        alertas.forEach(alerta => {
            alert(alerta.textContent.trim());
        });
    }
});
