#!/usr/bin/env python3

import math
import argparse
import yaml
from pathlib import Path
import itertools
import logging
import os

from KicadModTree import (
    Footprint,
    FootprintType,
    Pad,
    PolygonLine,
    Property,
    RectLine,
    RoundRadiusHandler,
    Text,
)
from kilibs.geom import Direction, Vector2D
from scripts.tools.nodes import pin1_arrow
from scripts.tools.declarative_def_tools import (
    ast_evaluator,
    common_metadata,
    fp_additional_drawing,
)
from scripts.tools.footprint_generator import FootprintGenerator
from scripts.tools.global_config_files import global_config as GC

from string import ascii_uppercase


class BGAConfiguration:
    """
    A type that represents the configuration of a BGA footprint
    (probably from a YAML config block).

    Over time, add more type-safe accessors to this class, and replace
    use of the raw dictionary.
    """

    _spec_dictionary: dict
    metadata: common_metadata.CommonMetadata

    def __init__(self, spec: dict):
        self._spec_dictionary = spec

        self.metadata = common_metadata.CommonMetadata(spec)

        if "pitch" in spec:
            self.pitch = Vector2D(spec["pitch"], spec["pitch"])
        elif "pitch_x" in spec and "pitch_y" in spec:
            self.pitch = Vector2D(spec["pitch_x"], spec["pitch_y"])
        else:
            raise KeyError("Either pitch or both pitch_x and pitch_y must be given.")

        self.additional_drawings = (
            fp_additional_drawing.FPAdditionalDrawing.from_standard_yaml(spec)
        )

    @property
    def spec_dictionary(self) -> dict:
        """
        Get the raw spec dictionary.

        This is only temporary, and can be piecewise replaced by
        type-safe declarative definitions, but that requires deep changes
        """
        return self._spec_dictionary


class BGAGenerator(FootprintGenerator):
    def __init__(self, configuration, **kwargs):
        super().__init__(**kwargs)

        self.configuration = configuration

    def generateFootprint(self, device_params: dict, pkg_id: str, header_info: dict = None):
        # Thin wrapper around generateBGAFootprint
        logging.info(f"Generating BGA footprint: {pkg_id}")
        self.generateBGAFootprint(self.configuration, device_params, pkg_id, header_info)

    def generateBGAFootprint(self, config, fpParams, fpId, header_info):
        device_config = BGAConfiguration(fpParams)

        if "pad_diameter" in fpParams:
            pad_diameter = fpParams["pad_diameter"]
            logging.info(f"Pad size of {fpId} is set by the footprint definition. "
                  "This should only be done for manufacturer-specific footprints.")
        elif "ball_type" in fpParams and "ball_diameter" in fpParams:
            ball_diameter = fpParams["ball_diameter"]
            ball_type = fpParams["ball_type"]
            # IPC-7352 Table 3-11 Median (Nominal) Material Level B
            if ball_type == "collapsible":
                pad_diameter = round(0.8*ball_diameter, 2)
            elif ball_type == "non-collapsible":
                pad_diameter = round(1.1*ball_diameter, 2)
            else:
                raise KeyError(f"{fpId}: '{ball_type}' is an invalid ball type. Only "
                      "'collapsible' and 'non-collapsible' are accepted values. "
                      "Aborting.")
        elif "ball_type" in fpParams and "ball_diameter" not in fpParams:
            raise KeyError(f"{fpId}: Ball diameter is missing. Aborting.")
        elif "ball_diameter" in fpParams and "ball_type" not in fpParams:
            raise KeyError(f"{fpId}: Ball type is missing. Aborting.")
        else:
            raise KeyError(f"{fpId}: The config file must include 'ball_type' and "
                           "'ball_diameter' or 'pad_diameter'. Aborting.")

        fpParams["pad_size"] = [pad_diameter, pad_diameter]
        self._createFootprintVariant(config, device_config, fpId, header_info)

    def compute_stagger(self, lParams):
        staggered = lParams.get('staggered')
        pitch = lParams.get('pitch')

        if staggered and pitch is not None:
            height = pitch * math.sin(math.radians(60))
            if staggered.lower() == 'x':
                return pitch/2, height, 'x'
            elif staggered.lower() == 'y':
                return height, pitch/2, 'y'
            else:
                raise ValueError('staggered must be either "x" or "y"')

        pitchX = lParams.get('pitch_x', pitch)
        pitchY = lParams.get('pitch_y', pitch)

        if not (pitchX and pitchY):
            raise KeyError('Either pitch or both pitch_x and pitch_y must be given.')

        return pitchX, pitchY, None

    def _compose_fp_name(self, config: dict, device_config: BGAConfiguration,
                        fpId: str, header_info: dict) -> str:
        device_params = device_config.spec_dictionary

        if "name" in device_params:
            return device_params["name"]

        if device_params.get("name_equal_to_key"):
            return fpId

        # To facilitate iteration through the layouts create a list with main
        # and sublayouts
        layouts = [device_params] + device_params.get("secondary_layouts", [])

        # Compute number of balls + diverse suffix strings
        pitch_text = ""
        stagger_text = ""
        offcenter_text = ""
        balls = 0
        for layout in layouts:
            balls += self.makePadGrid(None, layout, config, device_params)
            if pitch := layout.get("pitch"):
                new_pitch_text = f"P{pitch}mm"
            else:
                pitch_x = layout.get("pitch_x")
                pitch_y = layout.get("pitch_y")
                if not (pitch_x and pitch_y):
                    raise KeyError("Either pitch or both pitch_x and pitch_y must "
                                   "be given.")
                new_pitch_text = f"P{pitch_x}x{pitch_y}mm"
            if not pitch_text.endswith(new_pitch_text):
                pitch_text += new_pitch_text
            if "staggered" in layout:
                stagger_text = "_Stagger"
            if "offset_x" in layout or "offset_y" in layout:
                offcenter_text = "_Offcenter"

        if device_config.metadata.custom_name_format:
            name_format = device_config.metadata.custom_name_format
        else:
            name_format = config["fp_name_bga_format_string_no_trailing_zero"]

        pad_suffix = ""
        if (device_params.get("include_pad_diameter_in_name")
            and "pad_diameter" in device_params):
            pad_diameter = device_params["pad_diameter"]
            pad_suffix = f"_Pad{pad_diameter}mm"

        ball_suffix = ""
        if (device_params.get("include_ball_diameter_in_name")
            and "ball_diameter" in device_params):
            ball_diameter = device_params["ball_diameter"]
            ball_suffix = f"_Ball{ball_diameter}mm"

        suffix = device_params.get("suffix", "")

        fp_name = name_format.format(
            man=device_config.metadata.manufacturer or header_info.get("manufacturer", ""),
            mpn=device_config.metadata.part_number or "",
            pkg=device_params.get("device_type", header_info["package_type"]),
            pincount=balls,
            size_x=device_params["body_size_x"],
            size_y=device_params["body_size_y"],
            nx=device_params["layout_x"],
            ny=device_params["layout_y"],
            pitch=pitch_text,
            ball_d=ball_suffix,
            pad_d=pad_suffix,
            stagger=stagger_text,
            offcenter=offcenter_text,
            suffix=suffix,
            suffix2="",
        ).replace("__", "_").lstrip("_")
        return fp_name

    def _createFootprintVariant(self, config, device_config: BGAConfiguration, fpId, header_info):
        # Pull out the old-style parameter dictionary
        fpParams = device_config.spec_dictionary

        evaluator_params = {
            "pitch": device_config.pitch,
        }

        fp_evaluator = ast_evaluator.ASTevaluator(symbols=evaluator_params)

        pkgX = fpParams["body_size_x"]
        pkgY = fpParams["body_size_y"]
        layoutX = fpParams["layout_x"]
        layoutY = fpParams["layout_y"]
        fFabRefRot = 0

        fp_name = self._compose_fp_name(config, device_config, fpId, header_info)
        f = Footprint(fp_name, FootprintType.SMD)
        if "mask_margin" in fpParams:
            f.setMaskMargin(fpParams["mask_margin"])
        if "paste_margin" in fpParams:
            f.setPasteMargin(fpParams["paste_margin"])
        if "paste_ratio" in fpParams:
            f.setPasteMarginRatio(fpParams["paste_ratio"])

        s1 = [1.0, 1.0]
        if pkgX < 4.3 and pkgY > pkgX:
            s2 = [min(1.0, round(pkgY / 4.3, 2))] * 2  # Y size is greater, so rotate F.Fab reference
            fFabRefRot = -90
        else:
            s2 = [min(1.0, round(pkgX / 4.3, 2))] * 2

        t1 = 0.15 * s1[0]
        t2 = 0.15 * s2[0]

        chamfer = self.global_config.fab_bevel.getChamferSize(min(pkgX, pkgY))

        crtYdOffset = self.global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.BGA)

        def crtYdRound(x):
            # Round away from zero for proper courtyard calculation
            neg = x < 0
            if neg:
                x = -x
            x = math.ceil(x * 100) / 100.0
            if neg:
                x = -x
            return x

        pitchX, pitchY, staggered = self.compute_stagger(fpParams)

        xCenter = 0.0
        xLeftFab = xCenter - pkgX / 2.0
        xRightFab = xCenter + pkgX / 2.0
        xChamferFab = xLeftFab + chamfer
        xPadLeft = xCenter - pitchX * ((layoutX - 1) / 2.0)
        xLeftCrtYd = crtYdRound(xCenter - (pkgX / 2.0 + crtYdOffset))
        xRightCrtYd = crtYdRound(xCenter + (pkgX / 2.0 + crtYdOffset))

        yCenter = 0.0
        yTopFab = yCenter - pkgY / 2.0
        yBottomFab = yCenter + pkgY / 2.0
        yChamferFab = yTopFab + chamfer
        yPadTop = yCenter - pitchY * ((layoutY - 1) / 2.0)
        yTopCrtYd = crtYdRound(yCenter - (pkgY / 2.0 + crtYdOffset))
        yBottomCrtYd = crtYdRound(yCenter + (pkgY / 2.0 + crtYdOffset))
        yRef = yTopFab - 1.0
        yValue = yBottomFab + 1.0

        wFab = self.global_config.fab_line_width
        wCrtYd = self.global_config.courtyard_line_width
        wSilkS = self.global_config.silk_line_width

        # silkOffset should comply with pad clearance as well
        yPadTopEdge = yPadTop - fpParams["pad_size"][1] / 2.0
        xPadLeftEdge = xPadLeft - fpParams["pad_size"][0] / 2.0

        xSilkOffset = max(self.global_config.silk_fab_offset,
                          xLeftFab + self.global_config.silk_pad_offset - xPadLeftEdge)
        ySilkOffset = max(self.global_config.silk_fab_offset,
                          yTopFab + self.global_config.silk_pad_offset - yPadTopEdge)

        silkSizeX = pkgX + 2 * (xSilkOffset - self.global_config.silk_fab_offset)
        silkSizeY = pkgY + 2 * (ySilkOffset - self.global_config.silk_fab_offset)

        silkChamfer = self.global_config.fab_bevel.getChamferSize(
            min(silkSizeX, silkSizeY)
        )

        xLeftSilk = xLeftFab - xSilkOffset
        xRightSilk = xRightFab + xSilkOffset
        xChamferSilk = xLeftSilk + silkChamfer
        yTopSilk = yTopFab - ySilkOffset
        yBottomSilk = yBottomFab + ySilkOffset
        yChamferSilk = yTopSilk + silkChamfer

        # Text
        f.append(Property(name=Property.REFERENCE, text="REF**", at=[xCenter, yRef],
                      layer="F.SilkS", size=s1, thickness=t1))
        f.append(Property(name=Property.VALUE, text=fp_name, at=[xCenter, yValue],
                      layer="F.Fab", size=s1, thickness=t1))
        f.append(Text(text='${REFERENCE}', at=[xCenter, yCenter],
                      layer="F.Fab", size=s2, thickness=t2, rotation=fFabRefRot))

        # Fab
        f.append(PolygonLine(polygon=[[xRightFab, yBottomFab],
                                      [xLeftFab, yBottomFab],
                                      [xLeftFab, yChamferFab],
                                      [xChamferFab, yTopFab],
                                      [xRightFab, yTopFab],
                                     [xRightFab, yBottomFab]],
                             layer="F.Fab", width=wFab))

        # Courtyard
        f.append(RectLine(start=[xLeftCrtYd, yTopCrtYd],
                          end=[xRightCrtYd, yBottomCrtYd],
                          layer="F.CrtYd", width=wCrtYd))

        # Silk

        arrow_apex = Vector2D(xLeftSilk, yTopSilk)
        min_arrow_size = wSilkS * 3
        arrow_size = max(min_arrow_size, crtYdOffset / 2)

        f.append(
            pin1_arrow.Pin1SilkScreenArrow45Deg(
                arrow_apex, Direction.SOUTHEAST, arrow_size, "F.SilkS", wSilkS
            )
        )

        f.append(PolygonLine(
            polygon=[
                [xChamferSilk, yTopSilk],
                [xRightSilk, yTopSilk],
                [xRightSilk, yBottomSilk],
                [xLeftSilk, yBottomSilk],
                [xLeftSilk, yChamferSilk]
            ],
            layer="F.SilkS", width=wSilkS
        ))

        # Pads
        balls = self.makePadGrid(f, fpParams, config, xCenter=xCenter, yCenter=yCenter)

        for layout in fpParams.get('secondary_layouts', []):
            balls += self.makePadGrid(f, layout, config, fpParams, xCenter=xCenter, yCenter=yCenter)

        dwg_nodes = fp_additional_drawing.create_additional_drawings(
            device_config.additional_drawings, self.global_config, fp_evaluator
        )
        f.extend(dwg_nodes)

        # If this looks like a CSP footprint, use the CSP 3dshapes library
        packageType = str(header_info.get('package_type', 'BGA')).upper()
        if packageType not in ['CSP', 'BGA']:
            print(f'Invalid package type "{packageType}" in file header. No footprint generated.')

        if staggered:
            pdesc = str(fpParams.get('pitch')) if 'pitch' in fpParams else f'{pitchX}x{pitchY}'
            sdesc = f'{staggered.upper()}-staggered '
        else:
            pdesc = str(pitchX) if pitchX == pitchY else f'{pitchX}x{pitchY}'
            sdesc = ''

        description_parts = [
            device_config.metadata.description,
            f"{pkgX}x{pkgY}mm",
            f"{balls} Ball",
            f"{sdesc}{layoutX}x{layoutY} Layout",
            f"{pdesc}mm Pitch",
            f"generated with kicad-footprint-generator {os.path.basename(__file__)}",
        ]

        if device_config.metadata.datasheet:
            description_parts.append(device_config.metadata.datasheet)

        f.description = ", ".join(description_parts)

        f.tags = [packageType, str(balls), pdesc]
        f.tags += device_config.metadata.compatible_mpns
        f.tags += device_config.metadata.additional_tags

        lib_name = f'Package_{packageType}'

        # #################### Output and 3d model ############################
        self.add_standard_3d_model_to_footprint(f, lib_name, fp_name)
        self.write_footprint(f, lib_name)

    def makePadGrid(self, f, lParams, config, fpParams={}, xCenter=0.0, yCenter=0.0):
        layoutX = lParams["layout_x"]
        layoutY = lParams["layout_y"]
        rowNames = lParams.get('row_names', fpParams.get('row_names', config['row_names']))[:layoutY]
        rowSkips = lParams.get('row_skips', [])
        areaSkips = lParams.get('area_skips', [])
        padSkips = {skip.upper() for skip in lParams.get('pad_skips', [])}
        pitchX, pitchY, staggered = self.compute_stagger(lParams)

        for row_start, col_start, row_end, col_end in areaSkips:
            rows = rowNames[rowNames.index(row_start.upper()):rowNames.index(row_end.upper())+1]
            cols = range(col_start, col_end+1)
            padSkips |= {f'{a}{b}' for a, b in itertools.product(rows, cols)}

        for row, skips in zip(rowNames, rowSkips):
            for skip in skips:
                if isinstance(skip, int):
                    padSkips.add(f'{row}{skip}')
                else:
                    padSkips |= {f'{row}{skip}' for skip in range(*skip)}

        if (first_ball := lParams.get('first_ball')):
            if not staggered:
                raise ValueError('first_ball only makes sense for staggered layouts.')

            if first_ball not in ('A1', 'B1', 'A2'):
                raise ValueError('first_ball must be "A1" or "A2".')

            skip_even = (first_ball != 'A1')

            for row_num, row in enumerate(rowNames):
                for col in range(layoutX):
                    is_even = (row_num + col) % 2 == 0
                    if is_even == skip_even:
                        padSkips.add(f'{row}{col+1}')

        if f is None:
            return layoutX * layoutY - len(padSkips)

        padShape = lParams.get('pad_shape', fpParams.get('pad_shape', 'circle'))
        pasteShape = lParams.get('paste_shape', fpParams.get('paste_shape'))

        if pasteShape and pasteShape != padShape:
            layers = ['F.Cu', 'F.Mask']
        else:
            layers = Pad.LAYERS_SMT

        xOffset = lParams.get('offset_x', 0.0)
        yOffset = lParams.get('offset_y', 0.0)
        xPadLeft = xCenter - pitchX * ((layoutX - 1) / 2.0) + xOffset
        yPadTop = yCenter - pitchY * ((layoutY - 1) / 2.0) + yOffset

        for rowNum, row in enumerate(rowNames):
            rowSet = {col for col in range(1, layoutX+1) if f'{row}{col}' not in padSkips}
            for col in rowSet:
                f.append(Pad(
                    number="{}{}".format(row, col), type=Pad.TYPE_SMT,
                    fab_property=Pad.FabProperty.BGA,
                    shape=padShape,
                    at=[xPadLeft + (col-1) * pitchX, yPadTop + rowNum * pitchY],
                    size=lParams.get('pad_size') or fpParams['pad_size'],
                    layers=layers,
                    radius_ratio=self.global_config.roundrect_radius_handler
                ))

                if pasteShape and pasteShape != padShape:
                    # Footgun warning: When pcbnew renders a paste-only pad like this, it actually
                    # ignores all paste `margin settings both of the pad and of the footprint, and
                    # creates a stencil opening of exactly the size of the pad. Thus, we have to
                    # pre-compute paste margin here. Note that KiCad implements paste margin with an
                    # actual geometric offset, i.e. yielding a rounded rect for square pads. Thus,
                    # we have to implement similar offsetting logic here to stay consistent.

                    pasteMargin = lParams.get('paste_margin', fpParams.get('paste_margin', 0))
                    size = list(lParams.get('pad_size') or fpParams['pad_size'])
                    corner_ratio = self.global_config.roundrect_radius_handler.radius_ratio

                    if pasteShape == 'circle':
                        size[0] += 2*pasteMargin
                        size[1] += 2*pasteMargin

                    elif pasteShape == 'rect':
                        if pasteMargin <= 0:
                            size[0] += 2*pasteMargin
                            size[1] += 2*pasteMargin

                        else:
                            corner_ratio = pasteMargin / min(size)
                            size[0] += 2*pasteMargin
                            size[1] += 2*pasteMargin
                            pasteShape = 'roundrect'

                    elif pasteShape == 'roundrect':
                        corner_radius = min(size) * corner_ratio
                        size[0] += 2*pasteMargin
                        size[1] += 2*pasteMargin
                        corner_radius += pasteMargin

                        if corner_radius < 0:
                            pasteShape = 'rect'
                        else:
                            corner_ratio = corner_radius / min(size)

                    paste_radius_handler = RoundRadiusHandler(
                        radius_ratio=corner_ratio,
                    )

                    f.append(Pad(
                        number="", type=Pad.TYPE_SMT,
                        shape=pasteShape,
                        at=[xPadLeft + (col-1) * pitchX, yPadTop + rowNum * pitchY],
                        size=size,
                        layers=['F.Paste'],
                        round_radius_handler=paste_radius_handler
                    ))

        return layoutX * layoutY - len(padSkips)


def rowNameGenerator(seq):
    for n in itertools.count(1):
        for s in itertools.product(seq, repeat=n):
            yield ''.join(s)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='use config .yaml files to create footprints.')
    parser.add_argument('files', metavar='file', type=str, nargs='*',
                        help='list of files holding information about what devices should be created.')
    parser.add_argument('--global_config', type=str, nargs='?',
                        help='the config file defining how the footprint will look like. (KLC)',
                        default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--naming_config', type=str, nargs='?',
                         help='the config file defining footprint naming.', default='../package_config_KLCv3.yaml')

    args = FootprintGenerator.add_standard_arguments(parser)

    with open(args.naming_config, 'r') as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    # generate dict of A, B .. Y, Z, AA, AB .. CY less easily-confused letters
    rowNamesList = [x for x in ascii_uppercase if x not in 'IOQSXZ']
    configuration.update({'row_names': list(itertools.islice(rowNameGenerator(rowNamesList), 80))})

    FootprintGenerator.run_on_files(
        BGAGenerator,
        args,
        file_autofind_dir='size_definitions',
        configuration=configuration,
    )
