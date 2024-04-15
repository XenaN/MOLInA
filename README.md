# <img src="https://github.com/XenaN/MOLInA/assets/43779450/2f5cb40b-6593-4503-a750-bdb8b76c88d2" alt="Chemical Structure" width="30" height="30"> MOLInA: MOLecule Image Annotator <img src="https://github.com/XenaN/MOLInA/assets/43779450/3caa1116-d52f-4af4-af8e-7189b2d5e797" alt="malina" width="15" height="20"> 

**GUI for annotation of molecule images.**

## Description
While there are several applications and web services available for drawing molecules, many struggle to recognize chemical structures from images, especially when those structures are complex. Our application, MOLInA, is designed to help bridge this gap. By enabling users to annotate molecule images, MOLInA provides essential data that can be used to enhance the accuracy of machine learning models through transfer learning. This tool is particularly useful for improving the recognition of moderately complex to complex molecules, which are currently not well handled by existing models.

## Features and Functionality

In MOLInA, you can:
- 🖼️ Load images for annotation
- 🔬 Predict chemical structures using MolScribe (and soon, DECIMER)
- ➕ Add, 🔄 replace, or ❌ delete atoms and bonds
- 🧽 Clear annotations entirely
- ⌨️ Customize hotkeys
- 📄 Export to molfile format (currently in progress).

Coming soon:
- 🔋 Ability to add charge to molecules
- 🔄 DECIMER integration for improved predictions
- 📂 Batch processing for predicting structures in all images within a directory
- 💾 Options to save annotations in several styles.

## Application
Here's a look at the main interface of MOLInA:

When you open image

<img src="https://github.com/XenaN/MOLInA/assets/43779450/cdab674d-6372-4c18-9c7c-efbc671920a4" alt="screen1" width="754" height="428">

When you add atoms and bonds

<img src="https://github.com/XenaN/MOLInA/assets/43779450/152ea866-c6a7-4e7f-bfd5-e244b8203450" alt="screen1" width="754" height="428">

Choose model

<img src="https://github.com/XenaN/MOLInA/assets/43779450/334bc0ac-956a-4543-9a35-59bf141f33b4" alt="screen1" width="754" height="428">

Show (you can choose) recently opened image

<img src="https://github.com/XenaN/MOLInA/assets/43779450/e090dd1a-2680-47d8-aad6-2e9910af789a" alt="screen1" width="874" height="428">

## How To Use

Execute `> python -m molina`

Later you can download .exe to run application


## Installation

Clone repo to your computer and install via pip locally:

```bash
> git clone git@github.com:XenaN/MOLInA.git
> cd MOLInA
> pip install -e .
```

After that, download and place [MolScribe weights file](https://huggingface.co/yujieq/MolScribe/tree/main) to `models` directory.

## License

MOLInA is licensed under the GNU General Public License (GPL). This means that anyone is free to use, modify, and redistribute the software under the terms of the GPL.
