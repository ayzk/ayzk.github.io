// Mobile navigation toggle.
(function () {
    var btn = document.querySelector('.nav-toggle');
    var links = document.getElementById('nav-links');
    if (!btn || !links) return;

    btn.addEventListener('click', function () {
        var open = links.classList.toggle('is-open');
        btn.setAttribute('aria-expanded', String(open));
    });
})();
