document.addEventListener('DOMContentLoaded', () => {
    const grid        = document.getElementById('anime-grid');
    const loading     = document.getElementById('loading');
    const errorMsg    = document.getElementById('error-message');
    const statsBar    = document.getElementById('stats-bar');
    const controlsBar = document.getElementById('controls-bar');
    const searchInput = document.getElementById('search-input');
    const filterBtns  = document.querySelectorAll('.filter-btn');

    // Admin Elements
    const adminControls = document.getElementById('admin-controls');
    const btnLogout     = document.getElementById('btn-logout');
    const btnAddAnime   = document.getElementById('btn-add-anime');
    const btnLoginTop   = document.getElementById('btn-login-top');
    
    // Modals
    const editModal = document.getElementById('edit-modal');
    const addModal  = document.getElementById('add-modal');

    let allAnimes = [];
    let currentFilter = 'all';
    let editingIndex = null;
    
    // Check Auth
    const token = localStorage.getItem('kala_admin_token');
    if (token) {
        adminControls.classList.remove('hidden');
        if (btnLoginTop) btnLoginTop.style.display = 'none';
    }

    // ── Fetch ─────────────────────────────────────────────
    fetch(`data.json?t=${new Date().getTime()}`)
        .then(r => {
            if (!r.ok) throw new Error('Network error');
            return r.json();
        })
        .then(data => {
            allAnimes = data;
            loading.classList.add('hidden');
            grid.classList.remove('hidden');
            statsBar.classList.remove('hidden');
            controlsBar.classList.remove('hidden');
            renderStats(data);
            applyFilters();
        })
        .catch(err => {
            console.error('Error:', err);
            loading.classList.add('hidden');
            errorMsg.classList.remove('hidden');
        });

    // ── Stats ─────────────────────────────────────────────
    function renderStats(animes) {
        const total   = animes.length;
        const entera  = animes.filter(a => isEntera(a)).length;
        const eps     = animes
            .filter(a => !isEntera(a))
            .reduce((sum, a) => sum + (parseInt(a.purchased) || 0), 0);
        const pending = animes.filter(a => !isEntera(a) && (parseInt(a.purchased) || 0) === 0).length;

        document.getElementById('stat-total').textContent = total;
        document.getElementById('stat-entera').textContent = entera;
        document.getElementById('stat-eps').textContent = eps;
        document.getElementById('stat-pending').textContent = pending;
    }

    // ── Filters ───────────────────────────────────────────
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            applyFilters();
        });
    });

    searchInput.addEventListener('input', applyFilters);

    function applyFilters() {
        const query = searchInput.value.trim().toLowerCase();
        let filtered = allAnimes;

        if (currentFilter === 'entera') {
            filtered = filtered.filter(a => isEntera(a));
        } else if (currentFilter === 'purchased') {
            filtered = filtered.filter(a => !isEntera(a) && parseInt(a.purchased) > 0);
        }

        if (query) {
            filtered = filtered.filter(a => a.name.toLowerCase().includes(query));
        }

        renderCards(filtered);
    }

    function isEntera(anime) {
        return String(anime.purchased).toUpperCase() === 'ENTERA';
    }

    // ── Render Cards ──────────────────────────────────────
    function renderCards(animes) {
        grid.innerHTML = '';

        if (animes.length === 0) {
            grid.innerHTML = `<p style="color:var(--text-muted);grid-column:1/-1;text-align:center;padding:4rem 0;font-size:1rem;">
                No se encontraron animes con ese filtro.
            </p>`;
            return;
        }

        animes.forEach((anime) => {
            const realIndex = allAnimes.indexOf(anime);
            
            const card = document.createElement('div');
            card.className = 'anime-card';
            if (token) card.classList.add('is-admin');
            
            const purchased = isEntera(anime);
            const purchasedNum = parseInt(anime.purchased) || 0;

            let purchasedBadge;
            if (purchased) {
                purchasedBadge = `<span class="badge-entera">Entera</span>`;
            } else if (purchasedNum > 0) {
                purchasedBadge = `<span class="badge-count">${purchasedNum} cap${purchasedNum > 1 ? 's' : ''}</span>`;
            } else {
                purchasedBadge = `<span class="badge-count zero">Sin comprar</span>`;
            }

            const posterContent = anime.image
                ? `<img src="${anime.image}" alt="${anime.name}" class="poster-img" loading="lazy">`
                : `<div class="poster-placeholder">🎌</div>`;

            const epDisplay = anime.current_episode ?? '—';

            card.innerHTML = `
                <div class="poster-container">
                    ${posterContent}
                    <div class="poster-overlay"></div>
                    <div class="title-overlay">
                        <h2 class="anime-title">${anime.name}</h2>
                    </div>
                </div>
                <div class="card-body">
                    <div class="stat-row">
                        <span class="stat-row-label"><span class="stat-icon">▶</span> Capítulo actual</span>
                        <span class="ep-badge">${epDisplay}</span>
                    </div>
                    <div class="card-divider"></div>
                    <div class="stat-row">
                        <span class="stat-row-label"><span class="stat-icon">🛒</span> Chat compró</span>
                        ${purchasedBadge}
                    </div>
                </div>
            `;
            
            if (token) {
                card.addEventListener('click', () => openEditModal(realIndex));
            }
            grid.appendChild(card);
        });
    }

    // ── Image Upload Helper ───────────────────────────────
    async function uploadImageFile(fileInput) {
        if (!fileInput.files || fileInput.files.length === 0) return null;
        const file = fileInput.files[0];
        
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = async (e) => {
                const b64 = e.target.result;
                try {
                    const res = await fetch('/api/upload', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({
                            filename: file.name,
                            data: b64
                        })
                    });
                    const result = await res.json();
                    if (result.success) {
                        resolve(result.path);
                    } else {
                        alert("Error al subir imagen: " + result.error);
                        resolve(null);
                    }
                } catch (err) {
                    alert("Error de red subiendo imagen.");
                    resolve(null);
                }
            };
            reader.onerror = () => {
                alert("No se pudo leer el archivo.");
                resolve(null);
            };
            reader.readAsDataURL(file);
        });
    }

    // ── Admin Logic ───────────────────────────────────────
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            localStorage.removeItem('kala_admin_token');
            window.location.reload();
        });
    }

    if (btnAddAnime) {
        btnAddAnime.addEventListener('click', () => {
            document.getElementById('add-name').value = '';
            document.getElementById('add-img-file').value = '';
            addModal.classList.remove('hidden');
        });
    }

    window.stepInput = function(id, step) {
        const input = document.getElementById(id);
        if (input.value.toUpperCase() === 'ENTERA') {
            if (step > 0) return; 
            input.value = "0"; 
            return;
        }
        let val = parseInt(input.value) || 0;
        val += step;
        if (val < 0) val = 0;
        input.value = val;
    };

    async function saveToServer() {
        try {
            const res = await fetch('/api/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(allAnimes)
            });
            const result = await res.json();
            if (res.status === 401) {
                alert("Sesión expirada. Por favor, loguéate de nuevo.");
                localStorage.removeItem('kala_admin_token');
                window.location.href = 'login.html';
                return false;
            }
            if (!result.success) {
                alert("Error guardando datos: " + result.error);
                return false;
            }
            return true;
        } catch (err) {
            alert("Error de red");
            return false;
        }
    }

    // --- Add Modal ---
    document.getElementById('btn-cancel-add').addEventListener('click', () => addModal.classList.add('hidden'));
    
    document.getElementById('btn-save-add').addEventListener('click', async () => {
        const name = document.getElementById('add-name').value.trim();
        if (!name) return alert('El nombre es obligatorio');

        const btn = document.getElementById('btn-save-add');
        btn.textContent = 'Guardando...';
        btn.disabled = true;

        // Upload image if selected
        let imagePath = null;
        const fileInput = document.getElementById('add-img-file');
        if (fileInput.files.length > 0) {
            btn.textContent = 'Subiendo Imagen...';
            imagePath = await uploadImageFile(fileInput);
        }

        const newAnime = { name, current_episode: 0, purchased: "0", image: imagePath || "" };
        allAnimes.unshift(newAnime);

        btn.textContent = 'Guardando Datos...';
        if (await saveToServer()) {
            addModal.classList.add('hidden');
            applyFilters();
            renderStats(allAnimes);
        }
        btn.textContent = 'Añadir Anime';
        btn.disabled = false;
    });

    // --- Edit Modal ---
    function openEditModal(index) {
        editingIndex = index;
        const anime = allAnimes[index];
        
        document.getElementById('edit-modal-title').textContent = `Editar: ${anime.name}`;
        document.getElementById('edit-name').value = anime.name;
        document.getElementById('edit-ep').value = anime.current_episode || 0;
        document.getElementById('edit-buy').value = anime.purchased || 0;
        document.getElementById('edit-img-file').value = '';
        
        editModal.classList.remove('hidden');
    }

    document.getElementById('btn-cancel-edit').addEventListener('click', () => editModal.classList.add('hidden'));
    
    document.getElementById('btn-delete').addEventListener('click', async () => {
        if (!confirm('¿Seguro que querés borrar este anime?')) return;
        
        allAnimes.splice(editingIndex, 1);
        if (await saveToServer()) {
            editModal.classList.add('hidden');
            applyFilters();
            renderStats(allAnimes);
        }
    });

    document.getElementById('btn-save-edit').addEventListener('click', async () => {
        const btn = document.getElementById('btn-save-edit');
        btn.textContent = 'Guardando...';
        btn.disabled = true;

        const anime = allAnimes[editingIndex];
        anime.name = document.getElementById('edit-name').value.trim();
        anime.current_episode = document.getElementById('edit-ep').value.trim() || "0";
        anime.purchased = document.getElementById('edit-buy').value.trim() || "0";

        // Upload image if selected
        const fileInput = document.getElementById('edit-img-file');
        if (fileInput.files.length > 0) {
            btn.textContent = 'Subiendo Imagen...';
            const newPath = await uploadImageFile(fileInput);
            if (newPath) {
                anime.image = newPath;
            }
        }

        btn.textContent = 'Guardando Datos...';
        if (await saveToServer()) {
            editModal.classList.add('hidden');
            applyFilters();
            renderStats(allAnimes);
        }
        
        btn.textContent = 'Guardar Cambios';
        btn.disabled = false;
    });
});
