/* ============================================
   NIRVAG — Home Page Logic
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initScrollAnimations();
});

/** Navbar scroll effect */
function initNavbar() {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });

  // Mobile toggle
  const toggle = document.getElementById('mobileMenuToggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const links = document.querySelector('.nav-links');
      if (links) {
        links.classList.toggle('nav-links-open');
      }
    });
  }
}

/** Intersection Observer for scroll animations */
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

  document.querySelectorAll('.feature-card, .step-card, .cta-card').forEach(el => {
    observer.observe(el);
  });
}
