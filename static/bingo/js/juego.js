// Función para consultar la canción actual (GET)
async function fetchCurrentGame() {
    try {
        const response = await fetch('/api/current-game/');
        const data = await response.json();
        
        const songTitle = document.getElementById('current-song-title');
        if (data && data.current_song) {
            songTitle.innerText = data.current_song.name;
        } else {
            songTitle.innerText = "No hay partida activa";
        }
        
        // Si el usuario ya tiene un cartón cargado, lo actualiza de inmediato
        const userId = document.getElementById('user-id-input').value;
        if (userId) loadMyCard();
    } catch (error) {
        console.error("Error al obtener partida:", error);
    }
}

// Función para avanzar a la siguiente canción (POST)
async function nextSong() {
    try {
        await fetch('/api/next-song/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        });
        fetchCurrentGame(); // Refresca el estado global
    } catch (error) {
        console.error("Error al pasar de canción:", error);
    }
}

// Función para cargar el cartón de un jugador específico (GET)
async function loadMyCard() {
    const userId = document.getElementById('user-id-input').value;
    if (!userId) return;

    const gridContainer = document.getElementById('bingo-grid');
    
    try {
        const response = await fetch(`/api/my-card/${userId}/`);
        const items = await response.json();

        gridContainer.innerHTML = '';

        if (items.length === 0) {
            gridContainer.innerHTML = '<p>No tienes canciones asignadas.</p>';
            return;
        }

        items.forEach(item => {
            const songName = item.song ? item.song.name : "Desconocida";
            const isMarked = item.marked;
            
            // Si está marcada, añadimos la clase CSS '.marcada'
            const claseMarcada = isMarked ? 'marcada' : '';
            const checkIcon = isMarked ? ' ✅' : '';

            gridContainer.innerHTML += `
                <div class="casilla ${claseMarcada}">
                    <span>${songName} ${checkIcon}</span>
                </div>
            `;
        });
    } catch (error) {
        console.error("Error al cargar el cartón:", error);
    }
}

// Utilidad para extraer las cookies de seguridad CSRF de Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Ejecutar al cargar la página
window.onload = fetchCurrentGame;