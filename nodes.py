"""
This project is based on the original work from the repository:
https://github.com/badjeff/comfyui_lora_tag_loader

Original Author: badjeff
License: GPL-3.0 (GNU General Public License v3.0)

Modifications made by:wyjzp
Date of modifications:2024-11-27

Summary of changes:
- Updated the tag recognition pattern to support Chinese LoRA tags by adjusting the regex.
- Added a clarification about safe loading of LoRA files.

This modified version retains the original GPL-3.0 license. For further details, see:
https://www.gnu.org/licenses/gpl-3.0.en.html
"""
from pathlib import Path
import folder_paths
import re


# Import ComfyUI files
import comfy.sd
import comfy.utils

class LoraTagLoader:
    def __init__(self):
        self.loaded_lora = None
        # Modified the tag pattern to include support for Chinese characters and special symbols.
        self.tag_pattern = r"<[0-9a-zA-Z\u4e00-\u9fa5\:\_\-\.\s\/\(\)\\\\]+>"

    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "model": ("MODEL",),
                              "clip": ("CLIP", ),
                              "text": ("STRING", {"multiline": True}),
                              }}
    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "STRING")
    FUNCTION = "load_lora"

    CATEGORY = "loaders"

    def load_lora(self, model, clip, text):
        # print(f"\nLoraTagLoader input text: { text }")

        founds = re.findall(self.tag_pattern, text)
        # print(f"\nfoound lora tags: { founds }")

        if len(founds) < 1:
            return (model, clip, text)

        model_lora = model
        clip_lora = clip
        
        lora_files = folder_paths.get_filename_list("loras")
        for f in founds:
            tag = f[1:-1]
            pak = tag.split(":")
            type = pak[0]
            if type != 'lora':
                continue
            name = None
            if len(pak) > 1 and len(pak[1]) > 0:
                name = pak[1]
            else:
                continue
            wModel = wClip = 0
            try:
                if len(pak) > 2 and len(pak[2]) > 0:
                    wModel = float(pak[2])
                    wClip = wModel
                if len(pak) > 3 and len(pak[3]) > 0:
                    wClip = float(pak[3])
            except ValueError:
                continue
            if name == None:
                continue
            lora_name = None
            for lora_file in lora_files:
                if Path(lora_file).name.startswith(name) or lora_file.startswith(name):
                    lora_name = lora_file
                    break
            if lora_name == None:
                print(f"bypassed lora tag: { (type, name, wModel, wClip) } >> { lora_name }")
                continue
            print(f"detected lora tag: { (type, name, wModel, wClip) } >> { lora_name }")

            lora_path = folder_paths.get_full_path("loras", lora_name)
            lora = None
            if self.loaded_lora is not None:
                if self.loaded_lora[0] == lora_path:
                    lora = self.loaded_lora[1]
                else:
                    temp = self.loaded_lora
                    self.loaded_lora = None
                    del temp

            if lora is None:
                lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
                self.loaded_lora = (lora_path, lora)

            model_lora, clip_lora = comfy.sd.load_lora_for_models(model_lora, clip_lora, lora, wModel, wClip)

        plain_prompt = re.sub(self.tag_pattern, "", text)
        return (model_lora, clip_lora, plain_prompt)

NODE_CLASS_MAPPINGS = {
    "LoraTagLoader": LoraTagLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    # Loaders
    "LoraTagLoader": "Load LoRA Tag",
}
