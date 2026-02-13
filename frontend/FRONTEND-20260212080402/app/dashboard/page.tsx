'use client';

import { useAccount } from 'wagmi';
import { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

export default function DashboardPage() {
    const { address, isConnected } = useAccount();

    return (
        <>
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - NFTCollection</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-900 text-white">
    <div class="min-h-screen">
        <div class="fixed inset-y-0 left-0 w-64 bg-gray-800/50 border-r border-gray-700">
            <div class="p-6">
                <h2 class="text-xl font-bold gradient-text">NFTCollection</h2>
            </div>
            <nav class="mt-6">
                <a href="#" class="flex items-center px-6 py-3 text-gray-300 hover:bg-gray-700 hover:text-white">
                    <span class="mr-3">📊</span> Dashboard
                </a>
                <a href="#" class="flex items-center px-6 py-3 text-gray-300 hover:bg-gray-700 hover:text-white">
                    <span class="mr-3">💱</span> Swap
                </a>
                <a href="#" class="flex items-center px-6 py-3 text-gray-300 hover:bg-gray-700 hover:text-white">
                    <span class="mr-3">💰</span> Liquidity
                </a>
                <a href="#" class="flex items-center px-6 py-3 text-gray-300 hover:bg-gray-700 hover:text-white">
                    <span class="mr-3">📈</span> Portfolio
                </a>
            </nav>
        </div>
        <div class="ml-64 p-8">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div class="bg-gray-800 rounded-xl p-6">
                    <p class="text-sm text-gray-400 mb-2">Total Value Locked</p>
                    <p class="text-2xl font-bold">$42.5M</p>
                    <p class="text-sm text-green-400 mt-2">+12.3%</p>
                </div>
                <div class="bg-gray-800 rounded-xl p-6">
                    <p class="text-sm text-gray-400 mb-2">24h Volume</p>
                    <p class="text-2xl font-bold">$18.2M</p>
                    <p class="text-sm text-green-400 mt-2">+8.7%</p>
                </div>
                <div class="bg-gray-800 rounded-xl p-6">
                    <p class="text-sm text-gray-400 mb-2">Total Users</p>
                    <p class="text-2xl font-bold">12,345</p>
                    <p class="text-sm text-green-400 mt-2">+123 new</p>
                </div>
                <div class="bg-gray-800 rounded-xl p-6">
                    <p class="text-sm text-gray-400 mb-2">APY</p>
                    <p class="text-2xl font-bold">5.6%</p>
                    <p class="text-sm text-green-400 mt-2">+0.8%</p>
                </div>
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div class="bg-gray-800 rounded-xl p-6">
                    <h3 class="text-lg font-bold mb-4">Volume 7D</h3>
                    <canvas id="volumeChart"></canvas>
                </div>
                <div class="bg-gray-800 rounded-xl p-6">
                    <h3 class="text-lg font-bold mb-4">TVL History</h3>
                    <canvas id="tvlChart"></canvas>
                </div>
            </div>
            <div class="bg-gray-800 rounded-xl p-6">
                <h3 class="text-lg font-bold mb-4">Your Positions</h3>
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead>
                            <tr class="text-left text-gray-400 text-sm">
                                <th class="pb-4">Asset</th>
                                <th class="pb-4">Amount</th>
                                <th class="pb-4">Value</th>
                                <th class="pb-4">APY</th>
                                <th class="pb-4"></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="border-t border-gray-700">
                                <td class="py-4">ETH</td>
                                <td>10.5 ETH</td>
                                <td>$21,000</td>
                                <td class="text-green-400">4.2%</td>
                                <td><button class="text-blue-400 hover:text-blue-300">Manage</button></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <script>
        const ctx1 = document.getElementById('volumeChart').getContext('2d');
        new Chart(ctx1, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Volume',
                    data: [12, 19, 15, 17, 14, 13, 18],
                    borderColor: 'rgb(59, 130, 246)',
                    tension: 0.4
                }]
            }
        });
        const ctx2 = document.getElementById('tvlChart').getContext('2d');
        new Chart(ctx2, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'TVL',
                    data: [65, 78, 82, 85, 89, 92],
                    borderColor: 'rgb(16, 185, 129)',
                    tension: 0.4
                }]
            }
        });
    </script>
</body>
</html>
        </>
    );
}
