const fs = require('fs');

const planContent = fs.readFileSync('./reorganization_plan.csv', 'utf8');
const planLines = planContent.split('\n').slice(1);

const cyprusPlan = planLines
  .filter(line => line.trim())
  .map(line => {
    const parts = line.split(',');
    return {
      original_path: parts[1].replace(/"/g, ''),
      trip_name: parts[3],
    };
  })
  .filter(item => item.trip_name === 'cyprus');

// Get file sizes
const files = cyprusPlan
  .filter(item => fs.existsSync(item.original_path))
  .map(item => ({
    path: item.original_path,
    size: fs.statSync(item.original_path).size,
  }))
  .sort((a, b) => b.size - a.size);

console.log('Top 10 largest files:');
files.slice(0, 10).forEach((f, i) => {
  const name = f.path.replace(/\\/g, '/').split('/').pop();
  console.log((i+1) + '.', (f.size / 1024 / 1024).toFixed(2) + ' MB -', name);
});
