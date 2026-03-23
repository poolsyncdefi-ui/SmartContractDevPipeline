"use client";

export default function CreditScore() {
    return (
        <>
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Credit Scoring • BankingWeb3 Demo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .score-circle {
            transition: stroke-dashoffset 0.5s ease;
        }
        .metric-card {
            background: linear-gradient(145deg, #1a1e2a, #0f1219);
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 20px;
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            border-color: rgba(59,130,246,0.3);
        }
    </style>
</head>
<body class="bg-[#0A0C12] text-white">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold mb-2">Credit Scoring</h1>
                <p class="text-gray-400">On-chain creditworthiness assessment</p>
            </div>
            <div class="flex space-x-3">
                <span class="px-4 py-2 bg-blue-600 rounded-lg">Connect Wallet</span>
            </div>
        </div>

        <!-- Main Score -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div class="lg:col-span-2 metric-card p-8">
                <div class="flex items-center space-x-8">
                    <!-- Score Circle -->
                    <div class="relative w-32 h-32">
                        <svg class="w-32 h-32 transform -rotate-90">
                            <circle cx="64" cy="64" r="54" stroke="#2d3748" stroke-width="8" fill="none"/>
                            <circle class="score-circle" cx="64" cy="64" r="54" 
                                    stroke="#3b82f6" stroke-width="8" fill="none"
                                    stroke-dasharray="339.292" stroke-dashoffset="101.788"
                                    style="stroke-dashoffset: 101.788px;"/>
                        </svg>
                        <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
                            <span class="text-3xl font-bold">702</span>
                            <span class="text-sm text-gray-400 block">/850</span>
                        </div>
                    </div>
                    <!-- Score Info -->
                    <div>
                        <h2 class="text-2xl font-bold mb-2">Good Credit Score</h2>
                        <p class="text-gray-400 mb-2">Last updated: March 10, 2026</p>
                        <div class="flex space-x-2">
                            <span class="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">+12 pts</span>
                            <span class="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm">Top 15%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Quick Stats -->
            <div class="metric-card p-6">
                <h3 class="text-lg font-bold mb-4">Quick Stats</h3>
                <div class="space-y-4">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Total Transactions</span>
                        <span class="font-bold">847</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Volume</span>
                        <span class="font-bold">$124.5K</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Active Protocols</span>
                        <span class="font-bold">12</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Wallet Age</span>
                        <span class="font-bold">2.3 years</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Factors Grid -->
        <h2 class="text-2xl font-bold mb-6">Score Factors</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="metric-card p-6">
                <div class="flex items-center space-x-3 mb-4">
                    <span class="text-2xl">💰</span>
                    <h3 class="text-lg font-bold">Transaction History</h3>
                </div>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Consistency</span>
                        <span class="text-green-400">High</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Volume</span>
                        <span class="text-yellow-400">Medium</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Frequency</span>
                        <span class="text-green-400">High</span>
                    </div>
                </div>
            </div>
            <div class="metric-card p-6">
                <div class="flex items-center space-x-3 mb-4">
                    <span class="text-2xl">🏦</span>
                    <h3 class="text-lg font-bold">Protocol Engagement</h3>
                </div>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Lending</span>
                        <span class="text-green-400">Active</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">DEX Usage</span>
                        <span class="text-green-400">High</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Staking</span>
                        <span class="text-yellow-400">Low</span>
                    </div>
                </div>
            </div>
            <div class="metric-card p-6">
                <div class="flex items-center space-x-3 mb-4">
                    <span class="text-2xl">🔒</span>
                    <h3 class="text-lg font-bold">Risk Metrics</h3>
                </div>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Liquidation Risk</span>
                        <span class="text-green-400">0.2%</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Health Factor</span>
                        <span class="text-green-400">2.8</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Bad Debt</span>
                        <span class="text-green-400">None</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Activity -->
        <div class="mt-8 metric-card p-6">
            <h3 class="text-lg font-bold mb-4">Recent Activity</h3>
            <div class="space-y-3">
                <div class="flex justify-between items-center py-2 border-b border-gray-800">
                    <div>
                        <p class="font-medium">Deposited 5 ETH into Aave</p>
                        <p class="text-sm text-gray-400">2 hours ago</p>
                    </div>
                    <span class="text-green-400">+15 pts</span>
                </div>
                <div class="flex justify-between items-center py-2 border-b border-gray-800">
                    <div>
                        <p class="font-medium">Repaid 1,000 USDC loan</p>
                        <p class="text-sm text-gray-400">1 day ago</p>
                    </div>
                    <span class="text-green-400">+8 pts</span>
                </div>
                <div class="flex justify-between items-center py-2">
                    <div>
                        <p class="font-medium">Swapped 2 ETH for DAI on Uniswap</p>
                        <p class="text-sm text-gray-400">3 days ago</p>
                    </div>
                    <span class="text-green-400">+5 pts</span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        </>
    );
}
