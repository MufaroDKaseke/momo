

// Toggle Dark Mode
const modeToggler = $('#modeToggler');
const body = $('body');
console.log(modeToggler.children('i'));

modeToggler.on('click', (e) => {
  e.preventDefault();
  modeToggler.children('i').toggleClass('fa-moon fa-sun');
  body.toggleClass('darkmode');
});