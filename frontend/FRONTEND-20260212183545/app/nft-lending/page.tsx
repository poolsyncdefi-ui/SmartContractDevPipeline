"use client";

export default function NFTLending() {
    return (
        <>
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFT Lending • BankingWeb3</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#0A0C12] text-white">
    <div class="max-w-7xl mx-auto px-4 py-12">
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold mb-2">🖼️ NFT Lending</h1>
                <p class="text-gray-400">Empruntez contre vos NFT • Floor price lending</p>
            </div>
            <div class="flex space-x-4">
                <span class="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-full text-sm">
                    TVL: $45.2M
                </span>
                <span class="px-4 py-2 bg-green-500/20 text-green-400 rounded-full text-sm">
                    Taux: 4.8%
                </span>
            </div>
        </div>

        <!-- Your NFTs -->
        <div class="glass-card p-6 mb-8">
            <h2 class="text-xl font-bold mb-4">Vos NFT éligibles</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-white/5 rounded-xl p-4">
                    <div class="aspect-square bg-gradient-to-br from-blue-500/20 to-blue-600/20 rounded-lg mb-3 flex items-center justify-center">
                        <span class="text-3xl">🦍</span>
                    </div>
                    <h3 class="font-medium text-sm">BAYC #4592</h3>
                    <p class="text-xs text-gray-400">Bored Ape</p>
                    <div class="flex justify-between items-center mt-3">
                        <span class="text-sm font-bold">12.5 ETH</span>
                        <span class="text-xs text-green-400">LTV 65%</span>
                    </div>
                    <button class="w-full mt-3 px-3 py-1 bg-blue-600 rounded-lg text-sm">
                        Emprunter
                    </button>
                </div>
                <div class="bg-white/5 rounded-xl p-4">
                    <div class="aspect-square bg-gradient-to-br from-purple-500/20 to-purple-600/20 rounded-lg mb-3 flex items-center justify-center">
                        <span class="text-3xl">🎭</span>
                    </div>
                    <h3 class="font-medium text-sm">Art Block #123</h3>
                    <p class="text-xs text-gray-400">Fidenza</p>
                    <div class="flex justify-between items-center mt-3">
                        <span class="text-sm font-bold">8.2 ETH</span>
                        <span class="text-xs text-green-400">LTV 55%</span>
                    </div>
                    <button class="w-full mt-3 px-3 py-1 bg-blue-600 rounded-lg text-sm">
                        Emprunter
                    </button>
                </div>
                <div class="bg-white/5 rounded-xl p-4">
                    <div class="aspect-square bg-gradient-to-br from-pink-500/20 to-pink-600/20 rounded-lg mb-3 flex items-center justify-center">
                        <span class="text-3xl">👾</span>
                    </div>
                    <h3 class="font-medium text-sm">Azuki #789</h3>
                    <p class="text-xs text-gray-400">Azuki</p>
                    <div class="flex justify-between items-center mt-3">
                        <span class="text-sm font-bold">3.8 ETH</span>
                        <span class="text-xs text-green-400">LTV 60%</span>
                    </div>
                    <button class="w-full mt-3 px-3 py-1 bg-blue-600 rounded-lg text-sm">
                        Emprunter
                    </button>
                </div>
                <div class="bg-white/5 rounded-xl p-4">
                    <div class="aspect-square bg-gradient-to-br from-green-500/20 to-green-600/20 rounded-lg mb-3 flex items-center justify-center">
                        <span class="text-3xl">🐧</span>
                    </div>
                    <h3 class="font-medium text-sm">Pudgy #3456</h3>
                    <p class="text-xs text-gray-400">Pudgy</p>
                    <div class="flex justify-between items-center mt-3">
                        <span class="text-sm font-bold">1.2 ETH</span>
                        <span class="text-xs text-green-400">LTV 70%</span>
                    </div>
                    <button class="w-full mt-3 px-3 py-1 bg-blue-600 rounded-lg text-sm">
                        Emprunter
                    </button>
                </div>
            </div>
        </div>

        <!-- Active Loans -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="glass-card p-6">
                <h3 class="text-lg font-bold mb-4">📋 Vos emprunts</h3>
                <div class="space-y-4">
                    <div class="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                        <div class="flex items-center space-x-3">
                            <span class="text-2xl">🦍</span>
                            <div>
                                <p class="font-medium">BAYC #4592</p>
                                <p class="text-xs text-gray-400">Collatéral: 12.5 ETH</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="font-bold">8.1 ETH</p>
                            <p class="text-xs text-green-400">65% LTV</p>
                        </div>
                    </div>
                    <div class="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                        <div class="flex items-center space-x-3">
                            <span class="text-2xl">🎭</span>
                            <div>
                                <p class="font-medium">Art Block #123</p>
                                <p class="text-xs text-gray-400">Collatéral: 8.2 ETH</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="font-bold">4.5 ETH</p>
                            <p class="text-xs text-yellow-400">55% LTV</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="glass-card p-6">
                <h3 class="text-lg font-bold mb-4">📊 Market Overview</h3>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span>Blue Chip LTV</span>
                        <span class="font-medium">65-75%</span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2">
                        <div class="bg-green-500 h-2 rounded-full" style="width: 70%"></div>
                    </div>
                    <div class="flex justify-between mt-3">
                        <span>Collection LTV</span>
                        <span class="font-medium">40-55%</span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2">
                        <div class="bg-yellow-500 h-2 rounded-full" style="width: 48%"></div>
                    </div>
                </div>
                
                <div class="mt-6 p-4 bg-gradient-to-r from-yellow-900/30 to-red-900/30 rounded-xl border border-yellow-500/30">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <span class="text-2xl">⚠️</span>
                            <div>
                                <p class="font-medium">Liquidation imminent</p>
                                <p class="text-xs text-gray-400">BAYC #4592 • 78% LTV</p>
                            </div>
                        </div>
                        <button class="px-4 py-2 bg-yellow-600 rounded-lg text-sm">
                            Ajouter collatéral
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        </>
    );
}
