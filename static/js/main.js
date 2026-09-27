/**
 * Smart Flight Management System - Main JavaScript Application
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 6000);
    });

    // 2. Poll / Update unread notifications badge
    updateNotificationBadge();

    // 3. Setup mark notification read handler
    const markReadButtons = document.querySelectorAll('.mark-notif-read-btn');
    markReadButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const notifId = this.getAttribute('data-id');
            const itemElement = document.getElementById(`notif-item-${notifId}`);
            
            fetch(`/api/notifications/${notifId}/read`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
            .then(data => {
                if(data.success && itemElement) {
                    itemElement.classList.remove('unread');
                    this.remove();
                    updateNotificationBadge();
                }
            });
        });
    });

    // 4. Quick Flight Status Lookup Modal / AJAX
    const flightSearchBtn = document.getElementById('btnQuickFlightLookup');
    const flightSearchInput = document.getElementById('quickFlightInput');
    const flightStatusResult = document.getElementById('flightStatusResultContainer');

    if (flightSearchBtn && flightSearchInput) {
        flightSearchBtn.addEventListener('click', function() {
            const flightNo = flightSearchInput.value.trim();
            if (!flightNo) {
                alert('Please enter a flight number (e.g. AI-202 or SW-405)');
                return;
            }

            flightStatusResult.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2 text-muted">Checking flight radar...</p>
                </div>
            `;

            fetch(`/api/flight-status?flight_no=${encodeURIComponent(flightNo)}`)
                .then(res => {
                    if (!res.ok) throw new Error('Flight not found');
                    return res.json();
                })
                .then(data => {
                    flightStatusResult.innerHTML = `
                        <div class="card border-0 shadow-sm mt-3 bg-light">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <div>
                                        <h5 class="mb-0 fw-bold text-primary">${data.flight_number}</h5>
                                        <small class="text-muted">${data.airline}</small>
                                    </div>
                                    <span class="badge ${data.badge_class} fs-6 px-3 py-2">${data.status}</span>
                                </div>
                                <div class="row g-2 text-center my-3">
                                    <div class="col-5">
                                        <div class="fw-bold fs-5">${data.source}</div>
                                        <small class="text-muted d-block">${data.departure}</small>
                                    </div>
                                    <div class="col-2 d-flex align-items-center justify-content-center">
                                        <i class="bi bi-airplane-engines fs-4 text-primary"></i>
                                    </div>
                                    <div class="col-5">
                                        <div class="fw-bold fs-5">${data.destination}</div>
                                        <small class="text-muted d-block">${data.arrival}</small>
                                    </div>
                                </div>
                                <div class="d-flex justify-content-around border-top pt-2 mt-2 text-muted small">
                                    <span><i class="bi bi-door-open me-1"></i> Gate: <strong>${data.gate}</strong></span>
                                    <span><i class="bi bi-building me-1"></i> Terminal: <strong>${data.terminal}</strong></span>
                                </div>
                            </div>
                        </div>
                    `;
                })
                .catch(err => {
                    flightStatusResult.innerHTML = `
                        <div class="alert alert-warning mt-3">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            Flight "${flightNo}" was not found or has completed its schedule.
                        </div>
                    `;
                });
        });
    }
});

function updateNotificationBadge() {
    const badge = document.getElementById('headerNotifBadge');
    if (!badge) return;

    fetch('/api/notifications/unread-count')
        .then(res => res.json())
        .then(data => {
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        })
        .catch(() => {});
}
