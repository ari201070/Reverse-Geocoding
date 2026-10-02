export default {
  getAllPhotos() {
    // Mock 65 fotos válidas para dry-run (evita dependencia better-sqlite3)
    const mock=[];
    for(let i=0;i<65;i++){
      const d=new Date(2023,3,29,12,47+i%60,0);
      const dt=`${d.getFullYear()}:${String(d.getMonth()+1).padStart(2,'0')}:${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`;
      mock.push({ photo_name: `F:/2023/04-Abril/foto_${i}.jpg`, date_taken: dt, latitude: 43.65 + i*0.0001, longitude: 17.96 + i*0.0001, camera_heading: 90 });
    }
    return mock;
  }
};
