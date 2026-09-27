/**
 * Interactive Aircraft Seat Map Logic
 */

document.addEventListener('DOMContentLoaded', function () {
    const seatButtons = document.querySelectorAll('.seat-btn');
    const selectedSeatNumEl = document.getElementById('selectedSeatNumber');
    const selectedSeatClassEl = document.getElementById('selectedSeatClass');
    const selectedSeatExtraEl = document.getElementById('selectedSeatExtra');
    const selectedTotalFareEl = document.getElementById('selectedTotalFare');
    const hiddenSeatIdInput = document.getElementById('selected_seat_id');
    const btnProceedCheckout = document.getElementById('btnProceedCheckout');

    const baseFare = parseFloat(document.getElementById('flightBasePrice')?.value || 0);

    let currentSelectedSeat = null;

    seatButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            if (this.classList.contains('occupied')) {
                // Occupied feedback
                this.classList.add('shake');
                setTimeout(() => this.classList.remove('shake'), 400);
                return;
            }

            // Deselect previously selected
            if (currentSelectedSeat) {
                currentSelectedSeat.classList.remove('selected');
            }

            // Select this seat
            this.classList.add('selected');
            currentSelectedSeat = this;

            const seatId = this.getAttribute('data-seat-id');
            const seatNumber = this.getAttribute('data-seat-number');
            const seatClass = this.getAttribute('data-seat-class');
            const extraPrice = parseFloat(this.getAttribute('data-extra-price') || 0);

            // Update UI Sidebar
            if (selectedSeatNumEl) selectedSeatNumEl.textContent = seatNumber;
            if (selectedSeatClassEl) selectedSeatClassEl.textContent = seatClass;
            if (selectedSeatExtraEl) selectedSeatExtraEl.textContent = '₹' + extraPrice.toLocaleString('en-IN');
            
            const total = baseFare + extraPrice;
            if (selectedTotalFareEl) selectedTotalFareEl.textContent = '₹' + total.toLocaleString('en-IN');

            if (hiddenSeatIdInput) hiddenSeatIdInput.value = seatId;
            if (btnProceedCheckout) btnProceedCheckout.disabled = false;
        });
    });
});
