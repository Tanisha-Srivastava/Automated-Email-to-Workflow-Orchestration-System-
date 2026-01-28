from name_extractor import extract_names

# Load transcript
with open("data/transcript.txt") as f:
    lines = [l.strip() for l in f if l.strip()]

names = extract_names(lines)

roles = [
    "Project Manager",
    "UX Designer",
    "Frontend Engineer",
    "Backend Engineer",
    "QA Lead"
]

html = """<!DOCTYPE html>
<html>
<head>
  <title>Confirm Participants</title>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="styles.css">

</head>
<body>

<h2>Detected Participants</h2>

<form id="form">
"""

for name in names:
    html += f"""
  <div class="person">
    <strong>{name}</strong><br><br>
    Role:
    <select>
      {''.join(f"<option>{r}</option>" for r in roles)}
    </select><br>
    Email:
    <input type="email" placeholder="email@example.com" required>
    <hr>
  </div>
"""

html += """
<button type="button" id="saveBtn">Save Participants</button>
</form>

<script>
document.getElementById("saveBtn").addEventListener("click", function () {
  const people = document.querySelectorAll(".person");
  const participants = [];

  people.forEach(p => {
    const name = p.querySelector("strong").innerText;
    const role = p.querySelector("select").value;
    const email = p.querySelector("input").value;

    if (!email) {
      alert("Please enter email for " + name);
      return;
    }

    participants.push({ name: name, role: role, email: email });
  });

  const json = JSON.stringify(participants, null, 2);
  const blob = new Blob([json], { type: "application/json" });

  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "participants.json";
  a.click();
});
</script>

</body>
</html>
"""

with open("frontend/participants.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Generated frontend/participants.html")
