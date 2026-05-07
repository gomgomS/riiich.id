document.addEventListener('DOMContentLoaded', () => {
    const slides = document.querySelectorAll('.hero-slide');
    let current = 0;
    let isAnimating = false;

    if (slides.length === 0) return;

    function goToSlide(index) {
        if (isAnimating || index === current) return;
        isAnimating = true;

        slides[index].style.zIndex = 3;
        slides[current].style.zIndex = 2;

        slides[index].classList.add('active');

        setTimeout(() => {
            slides[current].classList.remove('active');
            slides[current].style.zIndex = 1;
            slides[index].style.zIndex = 2;

            current = index;
            isAnimating = false;
        }, 1200);
    }

    /* NAV */
    const nextBtn = document.querySelector('.hero-next');
    const prevBtn = document.querySelector('.hero-prev');

    if (nextBtn) {
        nextBtn.onclick = () => {
            goToSlide((current + 1) % slides.length);
        };
    }

    if (prevBtn) {
        prevBtn.onclick = () => {
            goToSlide((current - 1 + slides.length) % slides.length);
        };
    }

    /* AUTO with 4s delay BEFORE change */
    function autoSlide() {
        setTimeout(() => {
            goToSlide((current + 1) % slides.length);
            autoSlide(); // loop
        }, 4000); // ⬅️ WAIT 4 SECONDS
    }

    autoSlide();
});
