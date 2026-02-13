"use client";

export default function SavingsPods() {
    return (
        <>
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{{BANK_NAME}} • Banking Web3</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .glass { 
            background: rgba(15, 25, 35, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .glass-card {
            background: linear-gradient(145deg, rgba(20, 30, 45, 0.7), rgba(10, 20, 30, 0.9));
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-radius: 28px;
        }
        .neon-glow { box-shadow: 0 0 30px rgba(59, 130, 246, 0.15); }
        .animated-gradient {
            background: linear-gradient(45deg, {{PRIMARY_COLOR}}80, {{SECONDARY_COLOR}}80, {{ACCENT_COLOR}}80);
            background-size: 200% 200%;
            animation: gradient 15s ease infinite;
        }
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .virtual-card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .virtual-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
    </style>
</head>
<body class="bg-[#0A0F1A] text-white antialiased">
    <div class="min-h-screen">
        <!-- Top Navigation -->
        <div class="glass fixed top-0 left-0 right-0 z-50 px-6 py-4">
            <div class="max-w-7xl mx-auto flex justify-between items-center">
                <div class="flex items-center space-x-8">
                    <h1 class="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                        {{BANK_NAME}}
                    </h1>
                    <span class="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-xs font-medium">
                        ⚡ Web3 Banking
                    </span>
                </div>
                <div class="flex items-center space-x-6">
                    <!-- Voice Command -->
                    <button class="p-2 hover:bg-white/10 rounded-full transition" onclick="toggleVoice()">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"></path>
                        </svg>
                    </button>
                    <!-- Biometric Auth -->
                    <button class="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full">
                        <svg class="w-5 h-5" fill="none" stroke="white" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"></path>
                        </svg>
                    </button>
                    <!-- Avatar -->
                    <div class="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                        <span class="text-sm font-bold">{{USER_INITIALS}}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Dashboard -->
        <div class="max-w-7xl mx-auto pt-24 px-6 pb-12">
            <!-- Welcome + Balance -->
            <div class="flex justify-between items-start mb-8">
                <div>
                    <h2 class="text-3xl font-bold">Bonjour, {{USER_NAME}} 👋</h2>
                    <p class="text-gray-400 mt-2">{{DATE}} • Dernière connexion il y a 2 min</p>
                </div>
                <div class="flex space-x-3">
                    <span class="px-4 py-2 bg-green-500/10 text-green-400 rounded-full text-sm flex items-center">
                        <span class="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                        Wallet Connecté
                    </span>
                </div>
            </div>

            <!-- Balance Cards -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <div class="glass-card p-6 neon-glow col-span-2">
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="text-sm text-gray-400 mb-2">Solde Total</p>
                            <div class="flex items-end space-x-2">
                                <span class="text-4xl font-bold">${{TOTAL_BALANCE}}</span>
                                <span class="text-sm text-green-400 mb-1">+{{BALANCE_CHANGE}}%</span>
                            </div>
                            <div class="flex items-center mt-4 space-x-4">
                                <span class="text-xs text-gray-400">≈ {{ETH_BALANCE}} ETH</span>
                                <span class="text-xs text-gray-400">• ≈ {{BTC_BALANCE}} BTC</span>
                            </div>
                        </div>
                        <div class="flex space-x-2">
                            <button class="px-4 py-2 bg-blue-600 rounded-xl hover:bg-blue-700 transition">
                                Dépôt
                            </button>
                            <button class="px-4 py-2 bg-gray-700 rounded-xl hover:bg-gray-600 transition">
                                Retrait
                            </button>
                        </div>
                    </div>
                    <div class="mt-6 h-16" id="miniSparkline"></div>
                </div>
                
                <!-- Quick Actions -->
                <div class="glass-card p-6">
                    <h3 class="font-semibold mb-4">Actions rapides</h3>
                    <div class="grid grid-cols-2 gap-3">
                        <button class="p-3 bg-white/5 rounded-xl hover:bg-white/10 transition">
                            <span class="text-2xl mb-1 block">💳</span>
                            <span class="text-xs">Payer</span>
                        </button>
                        <button class="p-3 bg-white/5 rounded-xl hover:bg-white/10 transition">
                            <span class="text-2xl mb-1 block">📤</span>
                            <span class="text-xs">Envoyer</span>
                        </button>
                        <button class="p-3 bg-white/5 rounded-xl hover:bg-white/10 transition">
                            <span class="text-2xl mb-1 block">💰</span>
                            <span class="text-xs">Épargner</span>
                        </button>
                        <button class="p-3 bg-white/5 rounded-xl hover:bg-white/10 transition">
                            <span class="text-2xl mb-1 block">🔄</span>
                            <span class="text-xs">Swap</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Virtual Cards -->
            <div class="mb-8">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold">Cartes virtuelles</h3>
                    <button class="text-sm text-blue-400 hover:text-blue-300">+ Nouvelle carte</button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="bg-gradient-to-br from-indigo-900 to-indigo-800 rounded-2xl p-6 virtual-card">
                        <div class="flex justify-between items-start mb-8">
                            <span class="text-xs font-medium opacity-80">💳 Principale</span>
                            <span class="text-xs bg-white/20 px-3 py-1 rounded-full">Web3</span>
                        </div>
                        <div class="mb-6">
                            <span class="text-lg font-mono">•••• •••• •••• 4242</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <div>
                                <p class="text-xs opacity-70">Titulaire</p>
                                <p class="font-medium">{{USER_NAME}}</p>
                            </div>
                            <div>
                                <p class="text-xs opacity-70">Expire</p>
                                <p class="font-medium">12/28</p>
                            </div>
                        </div>
                    </div>
                    <div class="bg-gradient-to-br from-purple-900 to-purple-800 rounded-2xl p-6 virtual-card">
                        <div class="flex justify-between items-start mb-8">
                            <span class="text-xs font-medium opacity-80">🔄 Jetable</span>
                            <span class="text-xs bg-white/20 px-3 py-1 rounded-full">24h</span>
                        </div>
                        <div class="mb-6">
                            <span class="text-lg font-mono">•••• •••• •••• 1234</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <div>
                                <p class="text-xs opacity-70">Titulaire</p>
                                <p class="font-medium">{{USER_NAME}}</p>
                            </div>
                            <div>
                                <p class="text-xs opacity-70">Expire</p>
                                <p class="font-medium">Temporaire</p>
                            </div>
                        </div>
                    </div>
                    <div class="bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl p-6 virtual-card">
                        <div class="flex justify-between items-start mb-8">
                            <span class="text-xs font-medium opacity-80">🌍 Voyage</span>
                            <span class="text-xs bg-white/20 px-3 py-1 rounded-full">0% frais</span>
                        </div>
                        <div class="mb-6">
                            <span class="text-lg font-mono">•••• •••• •••• 5678</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <div>
                                <p class="text-xs opacity-70">Titulaire</p>
                                <p class="font-medium">{{USER_NAME}}</p>
                            </div>
                            <div>
                                <p class="text-xs opacity-70">Devise</p>
                                <p class="font-medium">EUR/USD</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Savings Pods -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div class="glass-card p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="font-semibold">Pockets d'épargne</h3>
                        <button class="text-xs text-blue-400">+ Nouveau</button>
                    </div>
                    <div class="space-y-4">
                        <div class="flex justify-between items-center">
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
                                    🏠
                                </div>
                                <div>
                                    <p class="text-sm font-medium">Projet Maison</p>
                                    <p class="text-xs text-gray-400">Objectif 50k €</p>
                                </div>
                            </div>
                            <div class="text-right">
                                <p class="text-sm font-bold">12,450 €</p>
                                <p class="text-xs text-green-400">24%</p>
                            </div>
                        </div>
                        <div class="flex justify-between items-center">
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center">
                                    ✈️
                                </div>
                                <div>
                                    <p class="text-sm font-medium">Voyage Japon</p>
                                    <p class="text-xs text-gray-400">Objectif 3k €</p>
                                </div>
                            </div>
                            <div class="text-right">
                                <p class="text-sm font-bold">2,150 €</p>
                                <p class="text-xs text-green-400">72%</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Round-up Savings -->
                <div class="glass-card p-6">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <h3 class="font-semibold">Arrondi automatique</h3>
                            <p class="text-xs text-gray-400 mt-1">Épargne 1.234 € ce mois-ci</p>
                        </div>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" class="sr-only peer" checked>
                            <div class="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:bg-blue-600"></div>
                        </label>
                    </div>
                    <div class="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                        <span class="text-sm">Multiplicateur</span>
                        <div class="flex space-x-2">
                            <button class="px-3 py-1 bg-blue-600 rounded-lg text-sm">2x</button>
                            <button class="px-3 py-1 bg-white/10 rounded-lg text-sm">4x</button>
                            <button class="px-3 py-1 bg-white/10 rounded-lg text-sm">10x</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Sparkline Chart
        var options = {
            series: [{ data: [31, 40, 28, 51, 42, 109, 100] }],
            chart: { type: 'area', height: 60, sparkline: { enabled: true } },
            stroke: { curve: 'smooth', width: 2 },
            colors: ['#3b82f6']
        };
        if(document.getElementById("miniSparkline")) {
            new ApexCharts(document.querySelector("#miniSparkline"), options).render();
        }

        // Voice Commands
        function toggleVoice() {
            alert("🎤 Voice command: 'Send 50€ to Marc'");
        }

        // Haptic Feedback
        document.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', () => {
                if (window.navigator.vibrate) window.navigator.vibrate(50);
            });
        });
    </script>
</body>
</html>
        </>
    );
}
