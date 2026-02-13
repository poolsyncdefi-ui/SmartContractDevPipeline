'use client';

import { useAccount, useContractWrite, usePrepareContractWrite } from 'wagmi';
import { useState } from 'react';

export default function MintPage() {
    const [quantity, setQuantity] = useState(1);
    const { address, isConnected } = useAccount();

    return (
        <>
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mint NFT - CryptoKitties Clone</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: #f8fafc; }
        .gradient-bg { background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); }
    </style>
</head>
<body class="antialiased">
    <div class="min-h-screen">
        <nav class="border-b border-gray-800">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex items-center">
                        <h1 class="text-xl font-bold gradient-bg bg-clip-text text-transparent">
                            CryptoKitties Clone
                        </h1>
                    </div>
                    <div class="flex items-center">
                        <w3m-button />
                    </div>
                </div>
            </div>
        </nav>
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
                <div class="space-y-6">
                    <div class="aspect-square rounded-2xl gradient-bg p-1">
                        <div class="bg-gray-900 rounded-2xl h-full flex items-center justify-center">
                            <div class="text-center p-8">
                                <div class="text-8xl mb-4">🖼️</div>
                                <h3 class="text-2xl font-bold mb-2">CryptoPunk #1234</h3>
                                <p class="text-gray-400">Collection: CryptoPunks</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-center space-x-4">
                        <div class="text-center">
                            <p class="text-3xl font-bold">10,000</p>
                            <p class="text-sm text-gray-400">Total Supply</p>
                        </div>
                        <div class="text-center">
                            <p class="text-3xl font-bold">3,456</p>
                            <p class="text-sm text-gray-400">Minted</p>
                        </div>
                        <div class="text-center">
                            <p class="text-3xl font-bold">0.05 ETH</p>
                            <p class="text-sm text-gray-400">Price</p>
                        </div>
                    </div>
                </div>
                <div class="space-y-8">
                    <div>
                        <h2 class="text-3xl font-bold mb-4">Mint Your NFT</h2>
                        <p class="text-gray-400">Unique digital collectibles on the Ethereum blockchain.</p>
                    </div>
                    <div class="bg-gray-800/50 rounded-2xl p-8 space-y-6">
                        <div>
                            <label class="block text-sm font-medium mb-2">Quantity</label>
                            <div class="flex items-center space-x-4">
                                <button class="w-10 h-10 rounded-lg bg-gray-700 hover:bg-gray-600 transition">-</button>
                                <input type="number" value="1" min="1" max="10" 
                                       class="w-20 px-3 py-2 bg-gray-700 rounded-lg text-center">
                                <button class="w-10 h-10 rounded-lg bg-gray-700 hover:bg-gray-600 transition">+</button>
                            </div>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Total Price</label>
                            <div class="text-2xl font-bold gradient-bg bg-clip-text text-transparent">0.05 ETH</div>
                        </div>
                        <button class="w-full gradient-bg text-white font-bold py-4 px-6 rounded-xl 
                                       hover:opacity-90 transition transform hover:scale-[1.02]">
                            Mint Now
                        </button>
                    </div>
                </div>
            </div>
        </main>
    </div>
</body>
</html>
        </>
    );
}
