const mineflayer = require('mineflayer');

const bot = mineflayer.createBot({
  host: 'antigravity.gg',
  username: 'TestBot' + Math.floor(Math.random() * 1000),
  version: '1.8.9',
  auth: 'offline'
});

bot.on('spawn', () => {
  console.log('✅ Conectado');
  bot.quit();
});

bot.on('error', (err) => {
  console.error('❌ Error:', err.message);
});

bot.on('kicked', (reason) => {
  console.log('Kicked:', reason);
});