/**
 * Order detail page — AJAX services/parts management & status changes.
 * Multi-select with checkboxes for adding services/parts.
 *
 * Globals from template: ORDER_ID, CSRF_TOKEN, SERVICES_DATA, PARTS_DATA, STATUS_LABELS
 */
(function () {
    'use strict';

    function csrf() { return CSRF_TOKEN || ''; }

    function postJSON(url, data) {
        var fd = new FormData();
        Object.keys(data).forEach(function (k) { fd.append(k, data[k]); });
        return fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrf() }, body: fd })
            .then(function (r) { return r.json(); });
    }

    function fmt(n) {
        return Math.round(parseFloat(n)).toLocaleString('ru-RU') + ' \u20bd';
    }

    function updateTotals(totals) {
        var ids = ['cost-services', 'cost-parts', 'cost-total', 'cost-final'];
        var keys = ['services', 'parts', 'total', 'final'];
        for (var i = 0; i < ids.length; i++) {
            var el = document.getElementById(ids[i]);
            if (el) el.textContent = fmt(totals[keys[i]]);
        }
    }

    function showAlert(msg, type) {
        var wrap = document.getElementById('ajax-alerts');
        if (!wrap) { alert(msg); return; }
        var div = document.createElement('div');
        div.className = 'alert alert-' + (type || 'danger') + ' alert-dismissible fade show small py-2';
        div.innerHTML = msg + '<button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>';
        wrap.appendChild(div);
        setTimeout(function () { div.style.opacity = '0'; setTimeout(function () { div.remove(); }, 400); }, 5000);
    }

    function escHtml(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

    // ── Build service checklist (grouped by category) ────────

    function buildServiceChecklist() {
        var container = document.getElementById('svc-checklist');
        if (!container || !SERVICES_DATA || !SERVICES_DATA.length) return;
        container.innerHTML = '';

        var groups = {};
        SERVICES_DATA.forEach(function (s) {
            if (!groups[s.category]) groups[s.category] = [];
            groups[s.category].push(s);
        });

        Object.keys(groups).forEach(function (cat) {
            var header = document.createElement('h6');
            header.className = 'text-muted small mt-2 mb-1';
            header.textContent = cat;
            container.appendChild(header);

            groups[cat].forEach(function (s) {
                var div = document.createElement('div');
                div.className = 'form-check svc-item py-1 border-bottom';
                div.innerHTML =
                    '<input class="form-check-input svc-cb" type="checkbox" value="' + s.id + '" ' +
                    'data-price="' + s.price + '" data-name="' + escHtml(s.name) + '" id="svc_' + s.id + '">' +
                    '<label class="form-check-label d-flex justify-content-between w-100" for="svc_' + s.id + '">' +
                    '<span>' + escHtml(s.name) + '</span>' +
                    '<strong class="text-nowrap ms-2">' + fmt(s.price) + '</strong>' +
                    '</label>';
                container.appendChild(div);
            });
        });

        // Update counters on change
        container.addEventListener('change', updateSvcCounter);
    }

    function updateSvcCounter() {
        var checked = document.querySelectorAll('.svc-cb:checked');
        var count = checked.length, total = 0;
        checked.forEach(function (cb) { total += parseFloat(cb.dataset.price); });
        var ce = document.getElementById('svc-selected-count');
        var te = document.getElementById('svc-selected-total');
        if (ce) ce.textContent = count;
        if (te) te.textContent = Math.round(total).toLocaleString('ru-RU');
    }

    // Search filter for services
    function bindSvcSearch() {
        var input = document.getElementById('svc-search');
        if (!input) return;
        input.addEventListener('input', function () {
            var q = this.value.toLowerCase();
            document.querySelectorAll('.svc-item').forEach(function (item) {
                var name = item.querySelector('label span').textContent.toLowerCase();
                item.style.display = name.includes(q) ? '' : 'none';
            });
        });
    }

    // ── Build parts checklist ────────────────────────────────

    function buildPartChecklist() {
        var container = document.getElementById('part-checklist');
        if (!container || !PARTS_DATA || !PARTS_DATA.length) return;
        container.innerHTML = '';

        PARTS_DATA.forEach(function (p) {
            var stockClass = p.stock <= 5 ? 'text-danger fw-semibold' : 'text-muted';
            var div = document.createElement('div');
            div.className = 'form-check part-item py-1 border-bottom';
            div.innerHTML =
                '<input class="form-check-input part-cb" type="checkbox" value="' + p.id + '" ' +
                'data-price="' + p.price + '" data-stock="' + p.stock + '" data-name="' + escHtml(p.name) + '" ' +
                'id="part_' + p.id + '"' + (p.stock <= 0 ? ' disabled' : '') + '>' +
                '<label class="form-check-label d-flex justify-content-between w-100" for="part_' + p.id + '">' +
                '<span>' + escHtml(p.name) +
                (p.part_number ? ' <small class="text-muted">(' + escHtml(p.part_number) + ')</small>' : '') +
                '</span>' +
                '<span class="text-nowrap ms-2">' +
                '<strong>' + fmt(p.price) + '</strong>' +
                ' <small class="' + stockClass + '">[' + p.stock + ' шт.]</small>' +
                '</span>' +
                '</label>';
            container.appendChild(div);
        });

        container.addEventListener('change', updatePartCounter);
    }

    function updatePartCounter() {
        var checked = document.querySelectorAll('.part-cb:checked');
        var count = checked.length, total = 0;
        checked.forEach(function (cb) { total += parseFloat(cb.dataset.price); });
        var ce = document.getElementById('part-selected-count');
        var te = document.getElementById('part-selected-total');
        if (ce) ce.textContent = count;
        if (te) te.textContent = Math.round(total).toLocaleString('ru-RU');
    }

    function bindPartSearch() {
        var input = document.getElementById('part-search');
        if (!input) return;
        input.addEventListener('input', function () {
            var q = this.value.toLowerCase();
            document.querySelectorAll('.part-item').forEach(function (item) {
                var name = item.querySelector('label span').textContent.toLowerCase();
                item.style.display = name.includes(q) ? '' : 'none';
            });
        });
    }

    // ── Add multiple services ────────────────────────────────

    function addServices() {
        var checked = document.querySelectorAll('.svc-cb:checked');
        if (!checked.length) { showAlert('Выберите хотя бы одну услугу.'); return; }

        var btn = document.getElementById('btn-add-service');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Добавление...';

        var promises = [];
        checked.forEach(function (cb) {
            promises.push(postJSON('/orders/' + ORDER_ID + '/add-service/', {
                service_id: cb.value,
                quantity: 1,
                price: cb.dataset.price,
            }));
        });

        Promise.all(promises).then(function (results) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-plus me-1"></i>Добавить выбранные';

            var added = 0, lastTotals = null;
            results.forEach(function (data) {
                if (data.success) {
                    added++;
                    lastTotals = data.totals;
                    var noRow = document.getElementById('no-services');
                    if (noRow) noRow.remove();
                    var tbody = document.querySelector('#services-table tbody');
                    var i = data.item;
                    var tr = document.createElement('tr');
                    tr.dataset.id = i.id;
                    tr.innerHTML =
                        '<td></td><td>' + escHtml(i.service_name) + '</td>' +
                        '<td>' + fmt(i.price) + '</td><td>' + i.quantity + '</td>' +
                        '<td class="fw-semibold">' + fmt(i.subtotal) + '</td>' +
                        '<td><button class="btn btn-sm btn-outline-danger btn-remove-service" data-id="' + i.id + '"><i class="fas fa-times"></i></button></td>';
                    tbody.appendChild(tr);
                }
            });

            if (lastTotals) updateTotals(lastTotals);
            if (added) showAlert('Добавлено услуг: ' + added, 'success');

            // Uncheck all and close
            checked.forEach(function (cb) { cb.checked = false; });
            updateSvcCounter();
            bootstrap.Modal.getInstance(document.getElementById('addServiceModal')).hide();
        }).catch(function () {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-plus me-1"></i>Добавить выбранные';
            showAlert('Сетевая ошибка.');
        });
    }

    // ── Add multiple parts ───────────────────────────────────

    function addParts() {
        var checked = document.querySelectorAll('.part-cb:checked');
        if (!checked.length) { showAlert('Выберите хотя бы одну запчасть.'); return; }

        var btn = document.getElementById('btn-add-part');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Добавление...';

        var promises = [];
        checked.forEach(function (cb) {
            promises.push(postJSON('/orders/' + ORDER_ID + '/add-part/', {
                spare_part_id: cb.value,
                quantity: 1,
                price_per_unit: cb.dataset.price,
            }));
        });

        Promise.all(promises).then(function (results) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-plus me-1"></i>Добавить выбранные';

            var added = 0, lastTotals = null, errors = [];
            results.forEach(function (data) {
                if (data.success) {
                    added++;
                    lastTotals = data.totals;
                    var noRow = document.getElementById('no-parts');
                    if (noRow) noRow.remove();
                    var tbody = document.querySelector('#parts-table tbody');
                    var i = data.item;
                    var tr = document.createElement('tr');
                    tr.dataset.id = i.id;
                    tr.innerHTML =
                        '<td></td><td>' + escHtml(i.part_name) + '</td>' +
                        '<td>' + fmt(i.price_per_unit) + '</td><td>' + i.quantity + '</td>' +
                        '<td class="fw-semibold">' + fmt(i.subtotal) + '</td>' +
                        '<td><button class="btn btn-sm btn-outline-danger btn-remove-part" data-id="' + i.id + '"><i class="fas fa-times"></i></button></td>';
                    tbody.appendChild(tr);
                } else {
                    errors.push(data.error || 'Ошибка');
                }
            });

            if (lastTotals) updateTotals(lastTotals);
            if (added) showAlert('Добавлено запчастей: ' + added, 'success');
            if (errors.length) showAlert('Ошибки: ' + errors.join('; '), 'warning');

            checked.forEach(function (cb) { cb.checked = false; });
            updatePartCounter();
            bootstrap.Modal.getInstance(document.getElementById('addPartModal')).hide();
        }).catch(function () {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-plus me-1"></i>Добавить выбранные';
            showAlert('Сетевая ошибка.');
        });
    }

    // ── Remove item (delegated) ──────────────────────────────

    function removeItem(e) {
        var svcBtn = e.target.closest('.btn-remove-service');
        var prtBtn = e.target.closest('.btn-remove-part');
        if (!svcBtn && !prtBtn) return;

        var isService = !!svcBtn;
        var btn = svcBtn || prtBtn;
        var id = btn.dataset.id;
        var type = isService ? 'услугу' : 'запчасть';

        if (!confirm('Удалить ' + type + '?')) return;
        btn.disabled = true;

        var url = '/orders/' + ORDER_ID + (isService ? '/remove-service/' : '/remove-part/') + id + '/';
        postJSON(url, {}).then(function (data) {
            if (data.success) {
                btn.closest('tr').remove();
                updateTotals(data.totals);
            } else {
                btn.disabled = false;
                showAlert(data.error || 'Ошибка удаления.');
            }
        });
    }

    // ── Status change ────────────────────────────────────────

    var pendingStatus = '';

    function onStatusButtonClick(e) {
        var btn = e.target.closest('.btn-status-change');
        if (!btn) return;
        pendingStatus = btn.dataset.status;
        var label = STATUS_LABELS[pendingStatus] || pendingStatus;
        document.getElementById('status-modal-text').textContent = 'Перевести заказ в статус \u00ab' + label + '\u00bb?';
        document.getElementById('status-comment').value = '';
        new bootstrap.Modal(document.getElementById('statusModal')).show();
    }

    function confirmStatusChange() {
        var btn = document.getElementById('btn-confirm-status');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>';

        postJSON('/orders/' + ORDER_ID + '/status/', {
            new_status: pendingStatus,
            comment: document.getElementById('status-comment').value,
        }).then(function (data) {
            if (!data.success) {
                btn.disabled = false;
                btn.textContent = 'Подтвердить';
                showAlert(data.error);
                return;
            }
            window.location.reload();
        }).catch(function () {
            btn.disabled = false;
            btn.textContent = 'Подтвердить';
            showAlert('Сетевая ошибка.');
        });
    }

    // ── Init (runs immediately — script is at bottom of body) ─

    function init() {
        buildServiceChecklist();
        buildPartChecklist();
        bindSvcSearch();
        bindPartSearch();

        var btnSvc = document.getElementById('btn-add-service');
        if (btnSvc) btnSvc.addEventListener('click', addServices);
        var btnPrt = document.getElementById('btn-add-part');
        if (btnPrt) btnPrt.addEventListener('click', addParts);

        document.addEventListener('click', removeItem);
        document.addEventListener('click', function (e) {
            if (e.target.closest('.btn-status-change')) onStatusButtonClick(e);
        });
        var btnConfirm = document.getElementById('btn-confirm-status');
        if (btnConfirm) btnConfirm.addEventListener('click', confirmStatusChange);
    }

    // Run immediately if DOM ready, otherwise wait
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
