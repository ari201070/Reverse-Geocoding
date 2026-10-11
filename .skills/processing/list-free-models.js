import fetch from 'node-fetch';

async function listFreeModels() {
  console.log("Fetching active free models from OpenRouter...");
  try {
    const res = await fetch('https://openrouter.ai/api/v1/models');
    if (!res.ok) {
      throw new Error(`Failed to fetch: ${res.status}`);
    }
    const data = await res.json();
    const freeModels = data.data.filter(model => {
      // Free models on OpenRouter usually have a pricing object with 0 prompt/completion cost
      const pricing = model.pricing;
      return pricing && parseFloat(pricing.prompt) === 0 && parseFloat(pricing.completion) === 0;
    });

    console.log(`Found ${freeModels.length} free models on OpenRouter:`);
    freeModels.forEach(m => {
      console.log(`- ${m.id} (${m.name})`);
    });
  } catch (e) {
    console.error("Error fetching models:", e.message);
  }
}

listFreeModels();
