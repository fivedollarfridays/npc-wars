/* Mobile banner dismiss logic */
(function() {
    var dismissed = localStorage.getItem('mobile-banner-dismissed');
    if (dismissed) {
        var banner = document.querySelector('.mobile-banner');
        if (banner) banner.style.display = 'none';
        return;
    }

    document.addEventListener('DOMContentLoaded', function() {
        var closeBtn = document.querySelector('.mobile-banner .close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                var banner = document.querySelector('.mobile-banner');
                if (banner) banner.style.display = 'none';
                localStorage.setItem('mobile-banner-dismissed', '1');
            });
        }
    });
})();
