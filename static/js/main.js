/**
 * Smart Health Monitoring and Appointment System
 * Main JavaScript Application Script
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss Bootstrap alert messages after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 6000);
    });

    // 2. Symptom Chip Interactive Selector
    initSymptomChips();

    // 3. Dynamic Appointment Slots Fetcher
    initAppointmentSlots();

    // 4. Live Queue Tracker
    initQueueTracker();

    // 5. Prevent double form submissions (e.g. double-clicking Register/Book/Login)
    initDoubleSubmitProtection();

    // 6. Dark mode toggle
    initThemeToggle();

    // 7. Fade-in sections on scroll
    initScrollFadeIn();
});

/**
 * Initializes interactive symptom chips in AI Triage Wizard
 */
function initSymptomChips() {
    const symptomChips = document.querySelectorAll('.symptom-chip');
    const symptomsInput = document.getElementById('id_symptoms');
    const selectedContainer = document.getElementById('selected-symptoms-container');
    const customSymptomInput = document.getElementById('custom-symptom-input');
    const addCustomBtn = document.getElementById('add-custom-symptom-btn');

    if (!symptomsInput) return;

    let selectedList = [];

    // Parse pre-existing symptoms if any
    if (symptomsInput.value) {
        selectedList = symptomsInput.value.split(',').map(s => s.trim()).filter(Boolean);
    }

    function syncInputAndUI() {
        symptomsInput.value = selectedList.join(', ');

        // Update chips UI
        symptomChips.forEach(chip => {
            const val = chip.getAttribute('data-symptom');
            if (selectedList.includes(val)) {
                chip.classList.add('selected');
            } else {
                chip.classList.remove('selected');
            }
        });

        // Update selected badges container
        if (selectedContainer) {
            selectedContainer.innerHTML = '';
            if (selectedList.length === 0) {
                selectedContainer.innerHTML = '<span class="text-muted small">No symptoms selected yet. Click from the list or add custom ones.</span>';
            } else {
                selectedList.forEach(s => {
                    const badge = document.createElement('span');
                    badge.className = 'badge bg-teal text-white p-2 me-1 mb-1 d-inline-flex align-items-center gap-1';
                    badge.style.backgroundColor = '#0F766E';
                    badge.innerHTML = `${s} <i class="bi bi-x-circle-fill ms-1" style="cursor: pointer;" title="Remove"></i>`;
                    badge.querySelector('i').addEventListener('click', () => {
                        removeSymptom(s);
                    });
                    selectedContainer.appendChild(badge);
                });
            }
        }
    }

    function toggleSymptom(symptom) {
        if (selectedList.includes(symptom)) {
            selectedList = selectedList.filter(s => s !== symptom);
        } else {
            selectedList.push(symptom);
        }
        syncInputAndUI();
    }

    function removeSymptom(symptom) {
        selectedList = selectedList.filter(s => s !== symptom);
        syncInputAndUI();
    }

    symptomChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const sym = chip.getAttribute('data-symptom');
            toggleSymptom(sym);
        });
    });

    if (addCustomBtn && customSymptomInput) {
        const addCustom = () => {
            const val = customSymptomInput.value.trim();
            if (val && !selectedList.includes(val)) {
                selectedList.push(val);
                customSymptomInput.value = '';
                syncInputAndUI();
            }
        };

        addCustomBtn.addEventListener('click', addCustom);
        customSymptomInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addCustom();
            }
        });
    }

    syncInputAndUI();
}

/**
 * Handles Dynamic Appointment Slots generation via API
 */
function initAppointmentSlots() {
    const doctorSelect = document.getElementById('id_doctor');
    const dateInput = document.getElementById('id_appointment_date');
    const timeInput = document.getElementById('id_appointment_time');
    const slotsContainer = document.getElementById('slots-container');
    const slotsLoading = document.getElementById('slots-loading');
    const slotsMessage = document.getElementById('slots-message');

    if (!doctorSelect || !dateInput || !slotsContainer) return;

    function fetchSlots() {
        const doctorId = doctorSelect.value;
        const dateVal = dateInput.value;

        if (!doctorId || !dateVal) {
            slotsContainer.innerHTML = '';
            if (slotsMessage) {
                slotsMessage.textContent = 'Please select both a doctor and date to view available appointment slots.';
                slotsMessage.style.display = 'block';
            }
            return;
        }

        if (slotsLoading) slotsLoading.style.display = 'block';
        if (slotsMessage) slotsMessage.style.display = 'none';
        slotsContainer.innerHTML = '';

        fetch(`/appointments/slots-api/?doctor_id=${doctorId}&date=${dateVal}`)
            .then(res => res.json())
            .then(data => {
                if (slotsLoading) slotsLoading.style.display = 'none';

                if (!data.available) {
                    if (slotsMessage) {
                        slotsMessage.textContent = data.message || 'Doctor not available on this date.';
                        slotsMessage.className = 'alert alert-warning py-2 small';
                        slotsMessage.style.display = 'block';
                    }
                    return;
                }

                if (!data.slots || data.slots.length === 0) {
                    if (slotsMessage) {
                        slotsMessage.textContent = 'No consultation time slots configured for this date.';
                        slotsMessage.className = 'alert alert-info py-2 small';
                        slotsMessage.style.display = 'block';
                    }
                    return;
                }

                data.slots.forEach(slot => {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'slot-btn';
                    btn.textContent = slot.display;
                    btn.setAttribute('data-time', slot.time);

                    if (!slot.is_available) {
                        btn.disabled = true;
                        btn.title = `Slot ${slot.status}`;
                    } else {
                        btn.addEventListener('click', () => {
                            document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('active'));
                            btn.classList.add('active');
                            if (timeInput) {
                                timeInput.value = slot.time;
                            }
                        });
                    }

                    if (timeInput && timeInput.value === slot.time && slot.is_available) {
                        btn.classList.add('active');
                    }

                    slotsContainer.appendChild(btn);
                });
            })
            .catch(err => {
                if (slotsLoading) slotsLoading.style.display = 'none';
                if (slotsMessage) {
                    slotsMessage.textContent = 'Failed to load time slots. Please try again.';
                    slotsMessage.style.display = 'block';
                }
                console.error('Error fetching slots:', err);
            });
    }

    doctorSelect.addEventListener('change', fetchSlots);
    dateInput.addEventListener('change', fetchSlots);

    // Initial check if values are already populated
    if (doctorSelect.value && dateInput.value) {
        fetchSlots();
    }
}

/**
 * Live Queue Tracker Polling
 */
function initQueueTracker() {
    const queueTrackerElem = document.getElementById('queue-live-tracker');
    if (!queueTrackerElem) return;

    const appointmentId = queueTrackerElem.getAttribute('data-appointment-id');
    const refreshBtn = document.getElementById('btn-refresh-queue');

    function updateQueue() {
        fetch(`/appointments/queue-api/${appointmentId}/`)
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    const posElem = document.getElementById('queue-pos-val');
                    const aheadElem = document.getElementById('queue-ahead-val');
                    const waitElem = document.getElementById('queue-wait-val');
                    const statusElem = document.getElementById('queue-status-val');
                    const updateElem = document.getElementById('queue-updated-val');

                    if (posElem) posElem.textContent = data.queue_position !== undefined ? data.queue_position : '-';
                    if (aheadElem) aheadElem.textContent = data.patients_ahead !== undefined ? data.patients_ahead : '-';
                    if (waitElem) waitElem.textContent = data.estimated_wait_time_minutes !== undefined ? `${data.estimated_wait_time_minutes} mins` : '-';
                    if (statusElem) statusElem.textContent = data.current_status || '-';
                    if (updateElem) updateElem.textContent = data.last_updated || 'Just now';
                }
            })
            .catch(err => console.error('Queue poll error:', err));
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Updating...';
            updateQueue();
            setTimeout(() => {
                refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i> Refresh Status';
            }, 800);
        });
    }

    // Auto poll every 25 seconds
    setInterval(updateQueue, 25000);
}

/**
 * 5. Prevents accidental double-submission of forms (e.g. a patient
 * double-clicking "Register" or "Book Appointment", or a doctor
 * double-clicking "Accept"). Disables the submit button and shows a
 * brief "Please wait..." state after the first click. A safety-net
 * timeout re-enables it in case the request never completes (e.g. a
 * dropped connection), so a genuine retry is always possible.
 */
function initDoubleSubmitProtection() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (form.dataset.submitted === 'true') {
                e.preventDefault();
                return;
            }
            // Let the browser's own HTML5 validation block invalid submissions first
            if (form.checkValidity && !form.checkValidity()) {
                return;
            }

            form.dataset.submitted = 'true';
            const submitControls = form.querySelectorAll('button[type="submit"], input[type="submit"]');
            submitControls.forEach(btn => {
                btn.disabled = true;
                if (btn.tagName === 'BUTTON' && !btn.dataset.originalHtml) {
                    btn.dataset.originalHtml = btn.innerHTML;
                    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Please wait...';
                }
            });

            setTimeout(() => {
                form.dataset.submitted = 'false';
                submitControls.forEach(btn => {
                    btn.disabled = false;
                    if (btn.dataset.originalHtml) {
                        btn.innerHTML = btn.dataset.originalHtml;
                    }
                });
            }, 12000);
        });
    });
}

/**
 * 6. Dark mode toggle. Preference is saved in localStorage so it persists
 * across page loads (this is a real deployed site, not a Claude artifact
 * preview, so localStorage is appropriate here).
 */
function initThemeToggle() {
    const THEME_KEY = 'shmasTheme';
    const toggleBtns = [
        document.getElementById('shmasThemeToggle'),
        document.getElementById('shmasThemeToggleGuest'),
    ].filter(Boolean);
    const icons = [
        document.getElementById('shmasThemeIcon'),
        document.getElementById('shmasThemeIconGuest'),
    ].filter(Boolean);

    if (toggleBtns.length === 0) return;

    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            icons.forEach(i => { i.classList.remove('bi-moon-stars'); i.classList.add('bi-sun'); });
        } else {
            document.documentElement.removeAttribute('data-theme');
            icons.forEach(i => { i.classList.remove('bi-sun'); i.classList.add('bi-moon-stars'); });
        }
    }

    let saved = 'light';
    try { saved = localStorage.getItem(THEME_KEY) || 'light'; } catch (e) { /* storage unavailable */ }
    applyTheme(saved);

    toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* storage unavailable */ }
        });
    });
}

/**
 * 7. Fade-in-on-scroll for elements with the .fade-in-section class.
 * Lightweight IntersectionObserver, no heavy animation libraries.
 */
function initScrollFadeIn() {
    const sections = document.querySelectorAll('.fade-in-section');
    if (sections.length === 0) return;

    if (!('IntersectionObserver' in window)) {
        sections.forEach(s => s.classList.add('is-visible'));
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15 });

    sections.forEach(s => observer.observe(s));
}
