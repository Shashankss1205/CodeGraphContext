// api/pypi.ts

export default async function handler(req: any, res: any) {
  const path = req.url?.replace("/api/pypi", "") || "";

  try {
    const response = await fetch(`https://pypistats.org/api${path}`);
    const data = await response.json();
    res.status(200).json(data);
  } catch (err) {
    res.status(500).json({ error: "Failed to fetch PyPI stats" });
  }
}
