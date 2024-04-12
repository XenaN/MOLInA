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

<img src="https://github.com/XenaN/MOLInA/assets/43779450/e651b6e3-f817-401e-9e1a-2b9c8c18f292" alt="screen1" width="874" height="432">

When you open and add atoms and bonds

<img src="https://github.com/XenaN/MOLInA/assets/43779450/4e8d390c-f4c6-4108-8669-58ed89c70df7" alt="screen1" width="874" height="432">

Choose model

<img src="https://github.com/XenaN/MOLInA/assets/43779450/e3ac0a7e-85b7-4497-a40a-0a29d997a7ad" alt="screen1" width="874" height="432">

Show (you can choose) recently opened image

<img src="https://github.com/XenaN/MOLInA/assets/43779450/a8145a45-0f92-42cd-a783-090f4015e7fc" alt="screen1" width="874" height="432">

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
