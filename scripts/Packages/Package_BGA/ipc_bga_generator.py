#!/usr/bin/env python3

import math
import os
import re
import sys
import argparse
import yaml
import warnings
from pathlib import Path
import itertools

# load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))

from KicadModTree import KicadFileHandler, Vector2D
from KicadModTree.nodes import Pad, Footprint, FootprintType, Model, Text, RectLine, PolygonLine
from scripts.tools.drawing_tools import TriangleArrowPointingSouthEast
from scripts.tools.declarative_def_tools import tags_properties

from string import ascii_uppercase


class BGAConfiguration:
    """
    A type that represents the configuration of a BGA footprint
    (probably from a YAML config block).

    Over time, add more type-safe accessors to this class, and replace
    use of the raw dictionary.
    """

    _spec_dictionary: dict
    compatible_mpns: tags_properties.TagsProperties
    additional_tags: tags_properties.TagsProperties

    def __init__(self, spec: dict):
        self._spec_dictionary = spec

        self.compatible_mpns = tags_properties.TagsProperties(
                spec.get('compatible_mpns', [])
        )

        # Generic addtional tags
        self.additional_tags = tags_properties.TagsProperties(
            spec.get(tags_properties.ADDITIONAL_TAGS_KEY, [])
        )

    @property
    def spec_dictionary(self) -> dict:
        """
        Get the raw spec dictionary.

        This is only temporary, and can be piecewise replaced by
        type-safe declarative definitions, but that requires deep changes
        """
        return self._spec_dictionary


class BGAGenerator:
    def generateFootprint(self, config, fpParams, fpId):
        createFp = False

        device_config = BGAConfiguration(fpParams)

        # use IPC-derived pad size if possible, then fall back to user-defined pads
        if "ball_type" in fpParams and "ball_diameter" in fpParams:
            try:
                padSize = configuration[fpParams["ball_type"]]
                try:
                    padSize = configuration[fpParams["ball_type"]][fpParams["ball_diameter"]]["max"]
                    fpParams["pad_size"] = [padSize, padSize]
                    createFp = True
                except KeyError as e:
                    self.error(f"{e}mm is an invalid ball diameter. See ipc_7351b_bga_land_patterns.yaml for valid values.")
            except KeyError as e:
                self.error(f"{e} is an invalid ball type. See ipc_7351b_bga_land_patterns.yaml for valid values.")

            if "pad_diameter" in fpParams:
                self.warn("Pad size is being derived using IPC rules even though pad diameter is defined.")
        elif "ball_type" in fpParams and "ball_diameter" not in fpParams:
            self.error("When ball_type is given, ball_diameter is required, but it is missing.")
        elif "ball_diameter" in fpParams and "ball_type" not in fpParams:
            self.error("When ball_diameter is given, ball_type is required, but it is missing.")
        elif "pad_diameter" in fpParams:
            fpParams["pad_size"] = [fpParams["pad_diameter"], fpParams["pad_diameter"]]
            if 'CSP' not in fpId and not re.fullmatch(r'[^_-]+_[^_-]*(BGA|CSP)[^_-]*-[0-9]+_.*', fpId):
                self.warn("Pads size is set by the footprint definition. This should only be done for manufacturer-specific footprints.")
            createFp = True
        else:
            self.error("The config file must either include both 'ball_type' and 'ball_diameter', or it must include 'pad_diameter'.")

        if createFp:
            self._createFootprintVariant(config, device_config, fpId)

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

    def _createFootprintVariant(self, config, device_config: BGAConfiguration, fpId):
        # Pull out the old-style parameter dictionary
        fpParams = device_config.spec_dictionary

        pkgX = fpParams["body_size_x"]
        pkgY = fpParams["body_size_y"]
        layoutX = fpParams["layout_x"]
        layoutY = fpParams["layout_y"]
        fFabRefRot = 0

        f = Footprint(fpId, FootprintType.SMD)
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

        chamfer = min(config['fab_bevel_size_absolute'], min(pkgX, pkgY) * config['fab_bevel_size_relative'])

        silkOffset = config['silk_fab_offset']
        crtYdOffset = config['courtyard_offset']['bga']

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

        wFab = configuration['fab_line_width']
        wCrtYd = configuration['courtyard_line_width']
        wSilkS = configuration['silk_line_width']

        # silkOffset should comply with pad clearance as well
        silkPadClearanceToSilkCentreline = config['silk_pad_clearance'] + wSilkS / 2.0
        yPadTopEdge = yPadTop - fpParams["pad_size"][1] / 2.0
        xPadLeftEdge = xPadLeft - fpParams["pad_size"][0] / 2.0

        xSilkOffset = max(silkOffset,
                          xLeftFab + silkPadClearanceToSilkCentreline - xPadLeftEdge)
        ySilkOffset = max(silkOffset,
                          yTopFab + silkPadClearanceToSilkCentreline - yPadTopEdge)

        silkSizeX = pkgX + 2 * (xSilkOffset - silkOffset)
        silkSizeY = pkgY + 2 * (ySilkOffset - silkOffset)

        silkChamfer = min(config['fab_bevel_size_absolute'],
                          min(silkSizeX, silkSizeY) * config['fab_bevel_size_relative'])

        xLeftSilk = xLeftFab - xSilkOffset
        xRightSilk = xRightFab + xSilkOffset
        xChamferSilk = xLeftSilk + silkChamfer
        yTopSilk = yTopFab - ySilkOffset
        yBottomSilk = yBottomFab + ySilkOffset
        yChamferSilk = yTopSilk + silkChamfer

        # Text
        f.append(Property(name=Property.REFERENCE, text="REF**", at=[xCenter, yRef],
                      layer="F.SilkS", size=s1, thickness=t1))
        f.append(Property(name=Property.VALUE, text=fpId, at=[xCenter, yValue],
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

        TriangleArrowPointingSouthEast(f, arrow_apex, arrow_size, "F.SilkS", wSilkS)

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

        # If this looks like a CSP footprint, use the CSP 3dshapes library
        packageType = 'CSP' if 'BGA' not in fpId and 'CSP' in fpId else 'BGA'

        f.append(Model(filename="{}Package_{}.3dshapes/{}.wrl".format(
                    config['3d_model_prefix'], packageType, fpId)))

        if staggered:
            pdesc = str(fpParams.get('pitch')) if 'pitch' in fpParams else f'{pitchX}x{pitchY}'
            sdesc = f'{staggered.upper()}-staggered '
        else:
            pdesc = str(pitchX) if pitchX == pitchY else f'{pitchX}x{pitchY}'
            sdesc = ''

        f.setDescription(f'{fpParams["description"]}, {pkgX}x{pkgY}mm, {balls} Ball, {sdesc}{layoutX}x{layoutY} Layout, {pdesc}mm Pitch, {fpParams["size_source"]}')  # NOQA

        f.tags = [packageType, str(balls), pdesc]
        f.tags += device_config.additional_tags.tags

        #if not re.fullmatch(r'.*-[0-9]+_[0-9.]+x[0-9.]+(x[0-9.]+)?mm(_Layout[0-9]+x[0-9]+)?(_P[0-9.]+(x[0-9.]+)?mm)(_.+)?', fpId):
        #    self.warn(f'KLC F3.4: Footprint name {fpId} does not match KLC F3.4 [PKG]-[Pincount]_[X]x[Y]x[Z]_Layout[Columns]x[Rows]_P[Pitch X]x[Pitch Y]_Ball[Ball]_Pad[Pad]_[NSMD/SMD]_[Modifiers]_[Options]')

        if (m := re.search(r'.+?-([0-9]+)_', fpId)):
            n_balls_name = int(m.group(1))
            if n_balls_name != balls:
                self.warn(f'KLC F3.4: Footprint {fpId} is named like it has {n_balls_name} balls, but the footprint actually has {balls} balls.')

            if n_balls_name != balls:
                self.warn(f'KLC F3.4: Footprint {fpId} is named like it has {n_balls_name} balls, but the footprint actually has {balls} balls.')
        
        else:
            self.warn(f'KLC F3.4: Footprint {fpId} is missing the ball count in the footprint name (e.g. "BGA-123" for 123 balls).')

        if (m := re.search(r'_([0-9.]+)x([0-9.]+)(x[0-9.]+)?(mm)?', fpId)):
            x, y = float(m.group(1)), float(m.group(2))
            if (round(x, 2), round(y, 2)) != (round(pkgX, 2), round(pkgY, 2)):
                self.warn(f'KLC F3.4: Size {m.group(0).strip("_")} in name of footprint {fpId} does not match the actual size of the footprint ({pkgX:.3f}x{pkgY:.3f}mm).')
            if m.group(4) is None:
                self.warn(f'KLC F3.4: Size {m.group(0).strip("_")} in name of footprint {fpId} is missing unit.')
        else:
            self.warn(f'KLC F3.4: Footprint {fpId} is missing the package size in the footprint name.')

        if (m := re.search(r'_Layout([0-9.]+)x([0-9.]+)', fpId)):
            x, y = float(m.group(1)), float(m.group(2))
            if (x, y) != (layoutX, layoutY):
                self.warn(f'KLC F3.4: Layout size {m.group(0).strip("_")} in name of footprint {fpId} does not match the actual ball layout size of the footprint ({layoutX}x{layoutY} balls).')
        elif not staggered:
            self.warn(f'KLC F3.4: Footprint {fpId} is missing the ball layout size in the name.')

        if (m := re.search(r'_P([0-9.]+)(x([0-9.]+))?(mm)?', fpId)):
            x, y = m.group(1), m.group(3)
            if float(x) != float(fpParams.get('pitch', pitchX)) or (y is not None and float(y) != float(fpParams.get('pitchY', pitchY))):
                self.warn(f'KLC F3.4: Pitch specification {m.group(0).strip("_")} in name of footprint {fpId} does not match the actual pitch of the footprint ({pitchX:.3f}x{pitchY:.3f} mm).')
            if m.group(4) is None:
                self.warn(f'KLC F3.4: Pitch specification {m.group(0).strip("_")} in name of footprint {fpId} is missing unit.')
        elif not staggered:
            self.warn(f'KLC F3.4: Footprint {fpId} is missing the ball pitch in the name.')

        if packageType == 'CSP' and not re.fullmatch(r'[^_-]+_[^_-]*(BGA|CSP)[^_-]*-[0-9]+_.*', fpId):
            self.warn(f"Manufacturer-specific CSP footprints should include the manufacturer's name at the start of their footprint name")

        outputDir = Path(f'Package_{packageType}.pretty')
        outputDir.mkdir(exist_ok=True)

        file_handler = KicadFileHandler(f)
        file_handler.writeFile(str(outputDir / f'{fpId}.kicad_mod'))

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
                    radius_ratio=config['round_rect_radius_ratio']
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
                    corner_ratio = config['round_rect_radius_ratio']

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

                    f.append(Pad(
                        number="{}{}".format(row, col), type=Pad.TYPE_SMT,
                        shape=pasteShape,
                        at=[xPadLeft + (col-1) * pitchX, yPadTop + rowNum * pitchY],
                        size=size,
                        layers=['F.Paste'],
                        radius_ratio=corner_ratio
                    ))

        return layoutX * layoutY - len(padSkips)


    def warn(self, *args):
        print('\033[38;5;214m' + ' '.join(map(str, args)) + '\033[0m', file=sys.stderr)


    def error(self, *args):
        print('\033[91m' + ' '.join(map(str, args)) + '\033[0m', file=sys.stderr)
        raise GeneratorError()


class GeneratorError(ValueError):
    pass


def rowNameGenerator(seq):
    for n in itertools.count(1):
        for s in itertools.product(seq, repeat=n):
            yield ''.join(s)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='use config .yaml files to create footprints.')
    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='list of files holding information about what devices should be created.')
    parser.add_argument('--global_config', type=str, nargs='?',
                        help='the config file defining how the footprint will look like. (KLC)',
                        default='../../tools/global_config_files/config_KLCv3.0.yaml')
    # parser.add_argument('--series_config', type=str, nargs='?',
    #                     help='the config file defining series parameters.', default='../package_config_KLCv3.yaml')
    parser.add_argument('--ipc_doc', type=str, nargs='?', help='IPC definition document',
                        default='ipc_7351b_bga_land_patterns.yaml')
    parser.add_argument('-v', '--verbose', action='count', help='set debug level')
    args = parser.parse_args()

    if args.verbose:
        DEBUG_LEVEL = args.verbose

    with open(args.global_config, 'r') as config_stream:
        try:
            configuration = yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    # with open(args.series_config, 'r') as config_stream:
        # try:
            # configuration.update(yaml.safe_load(config_stream))
        # except yaml.YAMLError as exc:
            # print(exc)

    with open(args.ipc_doc, 'r') as config_stream:
        try:
            configuration.update(yaml.safe_load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)

    # generate dict of A, B .. Y, Z, AA, AB .. CY less easily-confused letters
    rowNamesList = [x for x in ascii_uppercase if x not in 'IOQSXZ']
    configuration.update({'row_names': list(itertools.islice(rowNameGenerator(rowNamesList), 80))})

    generator = BGAGenerator()

    for filepath in args.files:
        with open(filepath, 'r') as command_stream:
            try:
                cmd_file = yaml.safe_load(command_stream)
            except yaml.YAMLError as exc:
                print(exc)
        for pkg in cmd_file:
            print(f'\033[38;5;244mGenerating footprint "{pkg}"...\033[0m', file=sys.stderr)
            try:
                generator.generateFootprint(configuration, cmd_file[pkg], pkg)
            except GeneratorError:
                print(f'\033[91mNo footprint generated.\033[0m')
