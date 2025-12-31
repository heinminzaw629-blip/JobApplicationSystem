// imports
const express = require("express");
const cors = require("cors");
const path = require("path");
const multer = require("multer");

// app init
const app = express();
app.use(cors());
app.use(express.json());

// multer setup
const allowedExt = new Set([".pdf", ".doc", ".docx", ".xlsx"]);

const upload = multer({
  dest: "uploads/",
  limits: { fileSize: 50 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();

    if (file.fieldname === "resume" || file.fieldname === "work_history") {
      if (!allowedExt.has(ext)) {
        return cb(new Error("Invalid resume/work history file type"));
      }
    }

    if (file.fieldname === "video") {
      if (
        !["video/mp4", "video/webm", "video/quicktime"].includes(file.mimetype)
      ) {
        return cb(new Error("Invalid video type"));
      }
    }

    cb(null, true);
  },
});

// test route
app.get("/", (req, res) => {
  res.json({ ok: true });
});

// application route
//app.post(
 // "/api/applications",
  //upload.fields([
   // { name: "resume", maxCount: 1 },
   // { name: "work_history", maxCount: 1 },
    //{ name: "video", maxCount: 1 },
  //]),
  //(req, res) => {
    //res.json({
    //  message: "Application received",
    //  body: req.body,
     // files: req.files,
    //});
  //}
//);
app.post(
  "/api/applications",
  upload.fields([
    { name: "resume", maxCount: 1 },
    { name: "work_history", maxCount: 1 },
    { name: "video", maxCount: 1 },
  ]),
  (req, res) => {
    const {
      name,
      email,
      phone,
      companyId,
      position,
      location,
      visa_type,
    } = req.body;

    res.json({
      ok: true,
      data: {
        name,
        email,
        phone,
        companyId,
        position,
        location,
        visa_type,
      },
      files: req.files,
    });
  }
);


// ⭐⭐⭐ SERVER START (အရမ်းအရေးကြီး)
app.listen(4000, () => {
  console.log("Backend running on http://localhost:4000");
});
