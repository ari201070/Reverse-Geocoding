const findPoi = require('./api/find-poi.js');

const req = {
    method: 'POST',
    body: {
        lat: -34.6037, // Obelisco Buenos Aires
        lng: -58.3816,
        radius: 500
    }
};

const res = {
    status: (code) => {
        console.log(`Status Set: ${code}`);
        return res;
    },
    json: (data) => {
        console.log("JSON Response:");
        console.log(JSON.stringify(data, null, 2));
    }
};

console.log("Testing API logic directly...");
findPoi(req, res).catch(console.error);
