export default async function handler(req, res) {
  const sym = (req.query.sym || "BTC").toUpperCase();
  const map = { SILVER: "XAG", HG1: "COPPER", USOIL: "WTI" };
  const fsym = map[sym] || sym;
  try {
    const r = await fetch(`https://cryptocompare.com{fsym}&tsym=USD&limit=70&aggregate=15`);
    const data = await r.json();
    res.setHeader("Access-Control-Allow-Origin", "*");
    return res.status(200).json(data);
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
