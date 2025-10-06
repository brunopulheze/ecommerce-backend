const express = require("express");
const Survey = require("../models/Survey");
const router = express.Router();

router.post("/", async (req, res) => {
    try {
        const survey = new Survey(req.body);
        await survey.save();
        res.status(201).json({ message: "Survey saved successfully" });
    } catch (err) {
        res.status(500).json({ error: "Failed to save survey" });
    }
});

module.exports = router;