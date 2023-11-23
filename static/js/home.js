let slideIndex = 0;

function showSlides() {
  const slides = document.querySelectorAll('.upcoming-slide');
  slides.forEach(slide => slide.style.display = 'none');
  slideIndex++;
  if (slideIndex > slides.length) slideIndex = 1;
  slides[slideIndex - 1].style.display = 'block';
  setTimeout(showSlides, 4000); // Change image every 2 seconds (adjust as needed)
}

showSlides();