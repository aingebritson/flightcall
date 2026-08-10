// Populates the county name in the page chrome.
//
// County app files are identical across counties: the county slug comes from
// the URL path (e.g. /washtenaw/ -> "washtenaw") and the display name from
// the root counties.json manifest, falling back to a title-cased slug so the
// page still reads correctly if the manifest fetch fails.
//
// Markup hooks:
//   [data-county-line]  -> "Washtenaw County, Michigan"
//   [data-county-name]  -> "Washtenaw County"
//   title[data-county-title] -> "Flightcall - Washtenaw County"
(function () {
    var segments = window.location.pathname.split('/').filter(Boolean);
    // Drop a trailing page filename (e.g. "hotspots.html") if present
    if (segments.length && /\.html$/.test(segments[segments.length - 1])) {
        segments.pop();
    }
    var slug = segments.length ? segments[segments.length - 1] : '';
    if (!slug) return;

    function titleCase(s) {
        return s.replace(/(^|[-_])([a-z])/g, function (m, sep, ch) {
            return (sep ? ' ' : '') + ch.toUpperCase();
        });
    }

    function apply(name) {
        var full = name + ' County';
        document.querySelectorAll('[data-county-line]').forEach(function (el) {
            el.textContent = full + ', Michigan';
        });
        document.querySelectorAll('[data-county-name]').forEach(function (el) {
            el.textContent = full;
        });
        if (document.querySelector('title[data-county-title]')) {
            document.title = 'Flightcall - ' + full;
        }
    }

    apply(titleCase(slug));

    fetch('../counties.json')
        .then(function (r) { return r.json(); })
        .then(function (manifest) {
            var counties = manifest.counties || [];
            for (var i = 0; i < counties.length; i++) {
                if (counties[i].slug === slug) {
                    apply(counties[i].name);
                    return;
                }
            }
        })
        .catch(function () {
            // Title-cased slug already applied — nothing to do
        });
}());
