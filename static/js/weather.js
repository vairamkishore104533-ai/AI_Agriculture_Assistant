function initWeather() {
    const container = document.getElementById("weather-container");
    if (!container) return;

    loadWeather();
}

function loadWeather() {
    const container = document.getElementById("weather-container");
    const adviceContainer = document.getElementById("weather-advice");
    const forecastContainer = document.getElementById("weather-forecast");

    fetch("/api/weather")
        .then((r) => r.json())
        .then((res) => {
            if (res.success) {
                renderWeather(res.weather, container);
                if (adviceContainer) {
                    adviceContainer.innerHTML = `
                        <div class="stat-card">
                            <h3 style="margin-bottom:12px;display:flex;align-items:center;gap:8px">
                                <span>🌾</span> ${adviceContainer.dataset.label || "AI Farming Advice"}
                            </h3>
                            <p style="color:var(--text-secondary);line-height:1.7">${res.advice}</p>
                        </div>`;
                }
                if (forecastContainer && res.weather.forecast) {
                    renderForecast(res.weather.forecast, forecastContainer);
                }
            }
        });
}

function renderWeather(weather, container) {
    if (!container) return;
    const icons = {
        clear: "☀️",
        clouds: "⛅",
        rain: "🌧️",
        thunderstorm: "⛈️",
        snow: "🌨️",
        mist: "🌫️",
        partly_cloudy: "⛅",
    };
    const icon = icons[weather.condition] || "🌤️";
    const lang = document.documentElement.lang || "en";

    container.innerHTML = `
        <div class="weather-card">
            <div class="weather-main">
                <div>
                    <div class="weather-temp">${weather.temperature}°C</div>
                    <div style="font-size:0.9rem;opacity:0.9">${icon} ${weather.condition}</div>
                </div>
            </div>
            <div class="weather-details">
                <div class="weather-detail">
                    <div class="detail-label">${lang === "ta" ? "ஈரப்பதம்" : "Humidity"}</div>
                    <div class="detail-value">${weather.humidity}%</div>
                </div>
                <div class="weather-detail">
                    <div class="detail-label">${lang === "ta" ? "காற்று" : "Wind"}</div>
                    <div class="detail-value">${weather.wind_speed} km/h</div>
                </div>
                <div class="weather-detail">
                    <div class="detail-label">${lang === "ta" ? "மழை" : "Rain"}</div>
                    <div class="detail-value">${weather.rain_probability}%</div>
                </div>
            </div>
        </div>`;
}

function renderForecast(forecast, container) {
    if (!container) return;
    container.innerHTML = forecast
        .map(
            (day) => `
            <div style="text-align:center;padding:12px;background:var(--bg-secondary);border-radius:var(--radius)">
                <div style="font-size:0.8rem;font-weight:600;color:var(--text-secondary)">${day.day}</div>
                <div style="font-size:1.3rem;font-weight:700;margin:8px 0">${day.temp}°C</div>
                <div style="font-size:0.75rem;color:var(--text-secondary)">🌧️ ${day.rain}%</div>
            </div>`
        )
        .join("");
}

document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("weather-container")) {
        initWeather();
    }
});
