require('dotenv').config();

const lat = -34.6037;
const lng = -58.3816;
const key = process.env.VITE_OPENCAGE_API_KEY;

// OpenCage expects latitude,longitude
const url = `https://api.opencagedata.com/geocode/v1/json?q=${lat},${lng}&key=${key}`;

console.log("Fetching: " + url.replace(key, 'HIDDEN_KEY'));

fetch(url)
  .then(res => res.json())
  .then(data => {
      if (data.results && data.results.length > 0) {
          console.log("Success!");
          console.log("Formatted:", data.results[0].formatted);
          console.log("Components:", data.results[0].components);
      } else {
          console.log("No results", data);
      }
  })
  .catch(console.error);
