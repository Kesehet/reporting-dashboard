// The chart suite consumes generated, uncommitted backend fixtures.
// Fail explicitly if a dedicated chart run lacks them; regular Jest runs
// can skip this suite without requiring Python and SQL-fixture dependencies.
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const folder = path.join(root, 'contract-results');
const inventoryFile = path.join(folder, 'inventory.json');

try {
  const inventory = JSON.parse(fs.readFileSync(inventoryFile, 'utf8'));
  if (!Array.isArray(inventory.cases) || inventory.cases.length === 0) {
    throw new Error('missing or empty cases inventory');
  }
  if (!Array.isArray(inventory.backend_handlers) || !Array.isArray(inventory.consumers)) {
    throw new Error('incomplete endpoint inventory');
  }
  for (const entry of inventory.cases) {
    if (!entry.file || !fs.existsSync(path.join(folder, 'cases', entry.file))) {
      throw new Error('missing generated response for ' + (entry.id || entry.file));
    }
  }
} catch (error) {
  console.error('Chart contract fixtures are missing or incomplete: ' + error.message);
  console.error('Generate them with: python scripts/run_chart_contracts.py');
  process.exitCode = 1;
}
