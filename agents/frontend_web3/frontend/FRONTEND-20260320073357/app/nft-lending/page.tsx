"use client";

export default function NFTLending() {
    return (
        <>
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFT Lending • BankingWeb3 Demo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .nft-card {
            background: linear-gradient(145deg, #1a1e2a, #0f1219);
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 20px;
            transition: all 0.3s ease;
            overflow: hidden;
        }
        .nft-card:hover {
            transform: translateY(-4px);
            border-color: #3b82f6;
            box-shadow: 0 10px 30px -10px #3b82f6;
        }
        .nft-image {
            height: 200px;
            background: linear-gradient(45deg, #2d3748, #1a202c);
            display: flex;
            align-items: center;
            justify-content: center;
        }
    </style>
</head>
<body class="bg-[#0A0C12] text-white">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold mb-2">NFT Lending</h1>
                <p class="text-gray-400">Borrow against your NFTs or lend to earn yield</p>
            </div>
            <div class="flex space-x-3">
                <button class="px-4 py-2 bg-blue-600 rounded-lg">Lend NFT</button>
                <button class="px-4 py-2 bg-purple-600 rounded-lg">Borrow</button>
            </div>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="nft-card p-4">
                <p class="text-sm text-gray-400">Total Loans</p>
                <p class="text-2xl font-bold">847</p>
            </div>
            <div class="nft-card p-4">
                <p class="text-sm text-gray-400">Volume</p>
                <p class="text-2xl font-bold">2,450 ETH</p>
            </div>
            <div class="nft-card p-4">
                <p class="text-sm text-gray-400">Avg LTV</p>
                <p class="text-2xl font-bold">42%</p>
            </div>
            <div class="nft-card p-4">
                <p class="text-sm text-gray-400">Avg Interest</p>
                <p class="text-2xl font-bold">8.5%</p>
            </div>
        </div>

        <!-- Active Loans -->
        <h2 class="text-2xl font-bold mb-4">Active Loans</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="nft-card">
                <div class="nft-image">
                    <span class="text-6xl">🖼️</span>
                </div>
                <div class="p-4">
                    <h3 class="text-xl font-bold mb-2">Bored Ape #8742</h3>
                    <div class="space-y-2 mb-4">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Loan Amount</span>
                            <span class="font-bold">15 ETH</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Interest</span>
                            <span class="text-green-400">6.5%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">LTV</span>
                            <span>35%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Duration</span>
                            <span>90 days</span>
                        </div>
                    </div>
                    <button class="w-full px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700">
                        Fund Loan
                    </button>
                </div>
            </div>
            <div class="nft-card">
                <div class="nft-image">
                    <span class="text-6xl">⚔️</span>
                </div>
                <div class="p-4">
                    <h3 class="text-xl font-bold mb-2">CryptoPunk #5209</h3>
                    <div class="space-y-2 mb-4">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Loan Amount</span>
                            <span class="font-bold">25 ETH</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Interest</span>
                            <span class="text-green-400">5.2%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">LTV</span>
                            <span>28%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Duration</span>
                            <span>60 days</span>
                        </div>
                    </div>
                    <button class="w-full px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700">
                        Fund Loan
                    </button>
                </div>
            </div>
            <div class="nft-card">
                <div class="nft-image">
                    <span class="text-6xl">👾</span>
                </div>
                <div class="p-4">
                    <h3 class="text-xl font-bold mb-2">Azuki #3021</h3>
                    <div class="space-y-2 mb-4">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Loan Amount</span>
                            <span class="font-bold">8 ETH</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Interest</span>
                            <span class="text-green-400">7.8%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">LTV</span>
                            <span>42%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Duration</span>
                            <span>30 days</span>
                        </div>
                    </div>
                    <button class="w-full px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700">
                        Fund Loan
                    </button>
                </div>
            </div>
        </div>

        <!-- Your Positions -->
        <h2 class="text-2xl font-bold mt-8 mb-4">Your Positions</h2>
        <div class="nft-card p-4">
            <div class="flex justify-between items-center">
                <div>
                    <p class="font-bold">You have no active positions</p>
                    <p class="text-sm text-gray-400">Start lending or borrowing to see your positions here</p>
                </div>
                <button class="px-4 py-2 bg-purple-600 rounded-lg">Browse NFTs</button>
            </div>
        </div>
    </div>
</body>
</html>
        </>
    );
}
