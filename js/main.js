
$(function() {

  // Calculate days before

  $('.postDateContainer').each(function() {
    const postDate = new Date($(this).attr('data-date'))
    const now  = new Date;
    let diff = now.getTime() - postDate.getTime();

    let days = diff / (1000 * 3600 * 24);

    if (days >= 7) {
      let weeks = Math.round(days / 7);
      $(this).html(weeks + ' weeks ago');
    } else if (days >= 30) {
      let months = Math.round(days / 30);
      $(this).html(months + ' months ago');
    } else {
      $(this).html(Math.round(days) + ' days ago');
    }

  });



  // Toggle Dark Mode
  const modeToggler = $('#modeToggler');
  const body = $('body');

  modeToggler.on('click', (e) => {
    e.preventDefault();
    modeToggler.children('i').toggleClass('fa-moon fa-sun');
    body.toggleClass('darkmode');
  });


});

  // Calculate post days
function getDays(postDate) {
  return Math.round(Math.abs(postDate - new Date()) / (1000 * 60 * 60 * 24));
}