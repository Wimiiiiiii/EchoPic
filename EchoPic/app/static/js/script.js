// Importation des modules Firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.8.1/firebase-app.js";
import { getAuth, onAuthStateChanged, signInWithPopup, GoogleAuthProvider, signInWithEmailAndPassword, createUserWithEmailAndPassword, sendPasswordResetEmail, signOut } from "https://www.gstatic.com/firebasejs/11.8.1/firebase-auth.js";

// Configuration Firebase
const firebaseConfig = {
    apiKey: "AIzaSyDLLUxHFTuN73015L2cR6m6pYtdVKICbp8",
    authDomain: "echopic-b679d.firebaseapp.com",
    projectId: "echopic-b679d",
    storageBucket: "echopic-b679d.firebasestorage.app",
    messagingSenderId: "1003205566040",
    appId: "1:1003205566040:web:61b5cee410aa7dd0c3f42d",
    measurementId: "G-X0F64N3GC7"
};

// Initialisation Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Écouteur d'état d'authentification
onAuthStateChanged(auth, user => {
    if (user) {
        // Utilisateur connecté
        if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
            window.location.href = '/search_interface'; // Redirige vers la page de recherche
        }
        // Si déjà sur /search_interface ou /results.html, ne rien faire
    } else {
        // Utilisateur non connecté
        if (window.location.pathname.startsWith('/search_interface') || window.location.pathname.startsWith('/results')) {
            window.location.href = '/'; // Redirige vers la page d'accueil/connexion
        } else if (document.getElementById('auth-container')){
            showAuthOptions(); // S'assure que les options d'auth sont visibles sur index.html
        }
    }
});

// Fonctions de navigation entre les différents formulaires
window.showEmailAuth = function() {
    document.getElementById('auth-container').classList.add('hidden');
    document.getElementById('email-login-container').classList.remove('hidden');
    document.getElementById('register-container').classList.add('hidden');
    document.getElementById('forgot-password-container').classList.add('hidden');
}

window.showAuthOptions = function() {
    document.getElementById('email-login-container').classList.add('hidden');
    document.getElementById('register-container').classList.add('hidden');
    document.getElementById('forgot-password-container').classList.add('hidden');
    document.getElementById('auth-container').classList.remove('hidden');
}

window.showRegister = function() {
    document.getElementById('email-login-container').classList.add('hidden');
    document.getElementById('register-container').classList.remove('hidden');
}

window.showForgotPassword = function() {
    document.getElementById('email-login-container').classList.add('hidden');
    document.getElementById('forgot-password-container').classList.remove('hidden');
}

// Fonctions d'authentification
window.loginWithGoogle = function() {
    const provider = new GoogleAuthProvider();
    signInWithPopup(auth, provider)
        .then(() => {
            showMessage("Connexion réussie! Redirection...", "success");
            window.location.href = '/search_interface';
        })
        .catch(error => {
            // Ne pas afficher de message d'erreur si l'utilisateur a simplement fermé la popup
            if (error.code !== 'auth/popup-closed-by-user' && error.code !== 'auth/cancelled-popup-request') {
                showMessage("Erreur: " + error.message, "error");
                console.error(error);
            }
        });
}

window.loginWithEmail = function() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    if (!email || !password) {
        showMessage('Veuillez remplir tous les champs', 'error');
        return;
    }

    signInWithEmailAndPassword(auth, email, password)
        .then(() => {
            showMessage("Connexion réussie! Redirection...", "success");
            window.location.href = '/search_interface';
        })
        .catch(error => {
            showMessage("Erreur: " + error.message, "error");
            console.error(error);
        });
}

window.registerWithEmail = function() {
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    
    if (!email || !password || !confirmPassword) {
        showMessage('Veuillez remplir tous les champs', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showMessage('Les mots de passe ne correspondent pas', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage("Le mot de passe doit contenir au moins 6 caractères", "error");
        return;
    }

    createUserWithEmailAndPassword(auth, email, password)
        .then(() => {
            showMessage("Inscription réussie! Redirection...", "success");
            window.location.href = '/search_interface';
        })
        .catch(error => {
            showMessage("Erreur: " + error.message, "error");
            console.error(error);
        });
}

window.sendPasswordResetEmail = function() {
    const email = document.getElementById('reset-email').value;
    
    if (!email) {
        showMessage('Veuillez entrer votre adresse email', 'error');
        return;
    }

    sendPasswordResetEmail(auth, email)
        .then(() => showMessage("Email de réinitialisation envoyé!", "success"))
        .then(() => setTimeout(() => {
            showEmailAuth();
        }, 1000))
        .catch(error => {
            showMessage("Erreur: " + error.message, "error");
            console.error(error);
        });
}

window.logout = function() {
    signOut(auth)
        .then(() => {
            showMessage("Déconnexion réussie. Redirection...", "success");
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        })
        .catch(error => {
            showMessage("Erreur lors de la déconnexion", "error");
            console.error(error);
        });
}

// Fonction utilitaire pour afficher les messages
window.showMessage = function(message, type = 'info') {
    const messageDiv = document.getElementById('message') || document.getElementById('auth-message');
    if (!messageDiv) return;
    
    messageDiv.textContent = message;
    messageDiv.classList.remove('hidden');
    
    // Définir la couleur en fonction du type de message
    messageDiv.className = `fixed top-4 right-4 p-4 rounded-md shadow-lg z-50 ${
        type === 'error' ? 'bg-red-500' : 
        type === 'success' ? 'bg-green-500' : 
        'bg-blue-500'
    } text-white`;
    
    // Cacher le message après 3 secondes
    setTimeout(() => {
        messageDiv.classList.add('hidden');
    }, 3000);
}

// Gestion du drag & drop pour l'upload d'images
document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('image-upload');
    const preview = document.getElementById('preview');

    if (dropZone && fileInput && preview) {
        // Empêcher le comportement par défaut du navigateur
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        // Mettre en évidence la zone de drop
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        // Gérer le drop
        dropZone.addEventListener('drop', handleDrop, false);

        // Gérer la sélection de fichier
        fileInput.addEventListener('change', handleFileSelect, false);
    }
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    const dropZone = document.getElementById('drop-zone');
    if (dropZone) {
        dropZone.classList.add('border-indigo-500');
    }
}

function unhighlight(e) {
    const dropZone = document.getElementById('drop-zone');
    if (dropZone) {
        dropZone.classList.remove('border-indigo-500');
    }
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        if (file.type.startsWith('image/')) {
            displayPreview(file);
        } else {
            showMessage('Veuillez sélectionner une image valide (JPG, PNG, WEBP)', 'error');
        }
    }
}

function displayPreview(file) {
    const preview = document.getElementById('preview');
    if (!preview) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        preview.src = e.target.result;
        preview.classList.remove('hidden');
    }
    reader.readAsDataURL(file);
}
