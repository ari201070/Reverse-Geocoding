const fs = require('fs');

const planContent = fs.readFileSync('./reorganization_plan.csv', 'utf8');
const planLines = planContent.split('\n').slice(1);

const cyprusPlan = planLines
  .filter(line => line.trim())
  .map(line => {
    const parts = line.split(',');
    return {
      original_path: parts[1].replace(/"/g, ''),
      proposed_target_path: parts[2].replace(/"/g, ''),
      trip_name: parts[3],
    };
  })
  .filter(item => item.trip_name === 'cyprus');

// Check target filenames
const targetNames = cyprusPlan.map(p => {
  const parts = p.proposed_target_path.replace(/\\/g, '/').split('/');
  return parts[parts.length - 1];
});

const uniqueNames = new Set(targetNames);
console.log('Total target filenames:', targetNames.length);
console.log('Unique target filenames:', uniqueNames.size);

// Find duplicates
const nameCount = {};
targetNames.forEach(n => {
  nameCount[n] = (nameCount[n] || 0) + 1;
});
const duplicates = Object.entries(nameCount).filter(([k, v]) => v > 1);
console.log('Duplicate target filenames:', duplicates.length);
if (duplicates.length > 0) {
  duplicates.forEach(([name, count]) => {
    console.log('  -', name, ':', count);
  });
}
