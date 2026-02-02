/** @type import('hardhat/config').HardhatUserConfig */
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

// Configuration des chemins
const paths = {
  sources: "./contracts",
  tests: "./test",
  cache: "./cache",
  artifacts: "./artifacts"
};

module.exports = {
  // Configuration Solidity
  solidity: {
    compilers: [
      {
        version: "0.8.20",
        settings: {
          optimizer: {
            enabled: true,
            runs: 200,
          },
          viaIR: false,
        },
      },
    ],
  },

  // Configuration des réseaux
  networks: {
    // Réseau local Hardhat (pour tests)
    hardhat: {
      chainId: 31337,
      allowUnlimitedContractSize: false,
      mining: {
        auto: true,
        interval: 0
      },
      accounts: {
        mnemonic: process.env.MNEMONIC || "test test test test test test test test test test test junk",
        accountsBalance: "10000000000000000000000" // 10,000 ETH
      }
    },

    // Localhost
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
    },

    // Sepolia Testnet
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || process.env.ALCHEMY_API_KEY || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 11155111,
      gas: "auto",
      gasPrice: "auto",
      gasMultiplier: 1.2,
    },

    // Mumbai Testnet (Polygon)
    mumbai: {
      url: process.env.MUMBAI_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 80001,
    },
  },

  // Configuration Etherscan pour vérification
  etherscan: {
    apiKey: {
      // Ethereum
      mainnet: process.env.ETHERSCAN_API_KEY || "",
      sepolia: process.env.ETHERSCAN_API_KEY || "",
      goerli: process.env.ETHERSCAN_API_KEY || "",
      // Polygon
      polygon: process.env.POLYGONSCAN_API_KEY || process.env.ETHERSCAN_API_KEY || "",
      polygonMumbai: process.env.POLYGONSCAN_API_KEY || process.env.ETHERSCAN_API_KEY || "",
    },
    customChains: [
      {
        network: "polygonMumbai",
        chainId: 80001,
        urls: {
          apiURL: "https://api-testnet.polygonscan.com/api",
          browserURL: "https://mumbai.polygonscan.com"
        }
      }
    ]
  },

  // Rapport de gas
  gasReporter: {
    enabled: (process.env.REPORT_GAS || "false") === "true",
    currency: process.env.GAS_REPORTER_CURRENCY || "USD",
    coinmarketcap: process.env.COINMARKETCAP_API_KEY || "",
    token: "ETH",
    gasPrice: 50,
    excludeContracts: [],
    src: "./contracts",
  },

  // Chemins
  paths: paths,

  // Configuration Mocha pour tests
  mocha: {
    timeout: 40000,
    color: true,
  },

  // Configuration Typechain
  typechain: {
    outDir: "./typechain-types",
    target: "ethers-v6",
  },
};
