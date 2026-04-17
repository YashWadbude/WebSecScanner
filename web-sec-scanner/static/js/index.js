/**
 * index.js - UI + OPTIONAL AUTH SYSTEM (FINAL CLEAN VERSION)
 */

const API_BASE = "http://127.0.0.1:5000";

document.addEventListener("DOMContentLoaded", () => {

    // ✅ Load user if logged in (no force login)
    loadUserIfLoggedIn();

    // =========================
    // 🎨 UI ANIMATIONS
    // =========================
    const cards = document.querySelectorAll('.card');

    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
            }
        });
    }, observerOptions);

    cards.forEach(card => {
        card.style.opacity = "0";
        card.style.transform = "translateY(20px)";
        card.style.transition = "all 0.6s cubic-bezier(0.23, 1, 0.32, 1)";
        scrollObserver.observe(card);
    });

    // =========================
    // 📍 ACTIVE NAV LINK
    // =========================
    const currentPath = window.location.pathname.split("/").pop();
    const navLinks = document.querySelectorAll('.navbar a');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.color = "var(--green-pro)";
            link.style.fontWeight = "700";
        }
    });

    console.log("WebSec Engine Ready (DB-based Auth)");
});


// =========================
// 🔐 LOAD USER (OPTIONAL)
// =========================
function loadUserIfLoggedIn() {
    const token = localStorage.getItem("token");

    if (!token) {
        // No login → clear any old leftover data (safety)
        clearClientData();
        return;
    }

    fetch(`${API_BASE}/profile`, {
        headers: {
            "Authorization": token
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.username) {
            document.getElementById("userDisplay").innerText = "👤 " + data.username;
        } else {
            throw new Error();
        }
    })
    .catch(() => {
        // Invalid/expired token → full cleanup
        clearClientData();
    });
}


// =========================
// 🚀 PROTECTED NAVIGATION
// =========================
function goToScan() {
    const token = localStorage.getItem("token");

    if (!token) {
        alert("⚠️ Please login to start scanning!");
        window.location.href = "login.html";
        return;
    }

    document.body.style.opacity = "0";
    document.body.style.transition = "opacity 0.5s ease";

    setTimeout(() => {
        window.location.href = "scan.html";
    }, 400);
}


// =========================
// 🔓 LOGOUT
// =========================
function logout() {
    clearClientData();
    window.location.href = "login.html";
}


// =========================
// 🧹 CLEAR CLIENT DATA
// =========================
function clearClientData() {
    localStorage.removeItem("token");

    // 🔥 Remove any old legacy data (important fix)
    localStorage.removeItem("scanData");
    localStorage.removeItem("scanHistory");
    localStorage.removeItem("lastScanProgress");
}