"""Current toothbrush case, native Fusion features driven by User Parameters.

Run inside Fusion. Lengths are mm; API geometry is cm.
Round threads: external on body neck, internal in cap. Native surface helix + circular sweep.
"""
import math
import traceback

SHORT_TEST = False
VERIFY_VARIANTS = False

BASE = {
    'outside_diameter': 51.4, 'body_height': 213.6, 'cap_height': 85.2,
    'wall_thickness': 4.5, 'bottom_thickness': 2.6,
    'outside_bottom_radius': 3.6, 'inside_bottom_radius': 2.8,
    'neck_height': 13.6, 'neck_wall': 1.8, 'cap_thread_offset': 0.4,
    'neck_lip_radius': 0.8, 'mouth_inside_radius': 0.7, 'shoulder_radius': 0.35,
    'thread_pitch': 4.68, 'thread_radius': 0.9, 'thread_embed': 0.1,
    'thread_clearance': 0.2, 'thread_offset': 2.45, 'thread_turns': 2,
    'cap_extra_turns': 0.5, 'cap_thread_phase': 90,
    'thread_end_tilt': 70,
    'cap_start_pivot_fraction': 0.4999920475545467 / 0.9,
    'cap_end_pivot_fraction': 0.46309897722625254 / 0.9,
    'body_start_pivot_fraction': 0.4999908101987566 / 0.9,
    'body_end_pivot_fraction': 0.334200842639421 / 0.9,
    'bottom_drain_diameter': 3, 'drain_target_web': 4,
    'drain_inner_fraction': 7 / 21.2, 'drain_outer_fraction': 14 / 21.2,
    'drain_outer_phase': 15, 'layout_gap': 12,
}
UNITLESS = {'thread_turns', 'cap_extra_turns', 'drain_inner_fraction', 'drain_outer_fraction',
            'cap_start_pivot_fraction', 'cap_end_pivot_fraction',
            'body_start_pivot_fraction', 'body_end_pivot_fraction'}
ANGLES = {'drain_outer_phase', 'cap_thread_phase', 'thread_end_tilt'}
DERIVED = {
    'outer_r': ('outside_diameter / 2', 'mm'),
    'body_inner_r': ('outer_r - wall_thickness', 'mm'),
    'neck_inner_r': ('body_inner_r', 'mm'),
    'neck_r': ('neck_inner_r + neck_wall', 'mm'),
    'body_shoulder_height': ('body_height - neck_height', 'mm'),
    'body_thread_centre_r': ('neck_r - thread_embed', 'mm'),
    'cap_inner_r': ('body_thread_centre_r + thread_radius + thread_clearance', 'mm'),
    'cap_wall': ('outer_r - cap_inner_r', 'mm'),
    'cap_thread_centre_r': ('cap_inner_r + thread_embed', 'mm'),
    'cap_thread_turns': ('thread_turns + cap_extra_turns', ''),
    'body_thread_height': ('thread_pitch * thread_turns', 'mm'),
    'cap_thread_height': ('thread_pitch * cap_thread_turns', 'mm'),
    'cap_thread_z': ('cap_height - neck_height - cap_thread_offset', 'mm'),
    'body_thread_z': ('body_shoulder_height + thread_offset', 'mm'),
    'thread_start_gap': ('thread_offset - thread_radius', 'mm'),
    'thread_end_gap': ('neck_height - thread_offset - body_thread_height - thread_radius', 'mm'),
    'drain_inner_r': ('body_inner_r * drain_inner_fraction', 'mm'),
    'drain_outer_r': ('body_inner_r * drain_outer_fraction', 'mm'),
    'drain_inner_count': ('max(3; floor(2 * PI * drain_inner_r / (bottom_drain_diameter + drain_target_web)))', ''),
    'drain_outer_count': ('max(3; floor(2 * PI * drain_outer_r / (bottom_drain_diameter + drain_target_web)))', ''),
    'assembly_height': ('body_shoulder_height + cap_height', 'mm'),
    'assembly_rotation': ('(assembly_height - cap_thread_z + thread_pitch * cap_thread_phase / (360 deg) - body_thread_z - thread_pitch / 2) / thread_pitch * 360 deg', 'deg'),
    'usable_length': ('assembly_height - 2 * bottom_thickness', 'mm'),
}
COMMENTS = {
    'outside_diameter': 'Đường kính ngoài chung của thân và nắp',
    'body_height': 'Cao thân gồm cổ mang ren ngoài',
    'cap_height': 'Cao nắp chụp ngoài cổ thân; có ren trong',
    'wall_thickness': 'Dày thành chính thân; quyết định lòng thân và lòng cổ thân',
    'bottom_thickness': 'Dày đáy phẳng của cả hai phần',
    'outside_bottom_radius': 'Bo đáy ngoài; giữ đáy phẳng ở tâm',
    'inside_bottom_radius': 'Bo đáy trong; giữ khoảng vật liệu quanh lỗ',
    'neck_height': 'Chiều dài cổ thân chui vào nắp',
    'neck_wall': 'Dày thành cổ thân, tối thiểu 1.8 mm',
    'cap_thread_offset': 'Độ lùi đầu ren nắp so với chiều dài cổ tính từ miệng',
    'cap_extra_turns': 'Số vòng ren nắp thêm so với thân; mặc định thêm nửa vòng như SCAD',
    'cap_thread_phase': 'Pha bắt đầu helix nắp; mặc định 90 độ như SCAD',
    'neck_lip_radius': 'Bo đầu cổ thân để dễ đưa vào miệng nắp',
    'mouth_inside_radius': 'Bo dẫn vào miệng nắp và mép trong đầu cổ thân',
    'shoulder_radius': 'Bo mép ngoài miệng nắp và vai thân',
    'thread_pitch': 'Bước ren chung; mỗi vòng tiến một bước theo trục',
    'thread_embed': 'Độ tâm tiết diện ren chìm vào cổ thân để Join liền khối',
    'thread_radius': 'Bán kính tiết diện ren tròn',
    'thread_turns': 'Số vòng ren thân; ren nắp thêm cap_extra_turns',
    'thread_offset': 'Khoảng từ vai thân tới tâm đầu ren',
    'thread_clearance': 'Hở theo bán kính từ đỉnh ren thân tới lòng trụ nắp; cần in thử',
    'thread_end_tilt': 'Góc nghiêng bốn mặt đầu ren; 70 độ theo bản F3D chỉnh tay',
    'cap_start_pivot_fraction': 'Trục đầu ren nắp lệch vào lòng theo tỷ lệ bán kính tiết diện',
    'cap_end_pivot_fraction': 'Trục cuối ren nắp lệch vào lòng theo tỷ lệ bán kính tiết diện',
    'body_start_pivot_fraction': 'Trục đầu ren thân lệch ra ngoài theo tỷ lệ bán kính tiết diện',
    'body_end_pivot_fraction': 'Trục cuối ren thân lệch ra ngoài theo tỷ lệ bán kính tiết diện',
    'bottom_drain_diameter': 'Đường kính lỗ thoát nước ở đáy thân',
    'drain_target_web': 'Khoảng vật liệu mục tiêu theo cung để tính số lỗ',
    'drain_inner_fraction': 'Tỷ lệ bán kính vòng lỗ trong so với bán kính lòng thân',
    'drain_outer_fraction': 'Tỷ lệ bán kính vòng lỗ ngoài so với bán kính lòng thân',
    'drain_outer_phase': 'Góc lệch vòng lỗ ngoài; giữ giữa 0 và 90 deg',
    'layout_gap': 'Khoảng cách giữa hai phần khi xếp cạnh nhau để in',
}


def defaults(short=False):
    return dict(BASE, body_height=31.6, cap_height=24) if short else dict(BASE)


def dimensions(p):
    outer=p['outside_diameter']/2
    inner=outer-p['wall_thickness']
    neck=inner+p['neck_wall']
    shoulder=p['body_height']-p['neck_height']
    male=neck-p['thread_embed']
    cap_inner=male+p['thread_radius']+p['thread_clearance']
    cap_turns=p['thread_turns']+p['cap_extra_turns']
    body_z=shoulder+p['thread_offset']
    cap_z=p['cap_height']-p['neck_height']-p['cap_thread_offset']
    assembly=shoulder+p['cap_height']
    rotation=(assembly-cap_z+p['thread_pitch']*p['cap_thread_phase']/360-body_z-p['thread_pitch']/2)/p['thread_pitch']*360
    r1,r2=inner*p['drain_inner_fraction'],inner*p['drain_outer_fraction']
    def count(r):
        return max(3,math.floor(2*math.pi*r/(p['bottom_drain_diameter']+p['drain_target_web'])))
    return dict(outer_r=outer,body_inner_r=inner,neck_r=neck,neck_inner_r=inner,
        cap_inner_r=cap_inner,cap_wall=outer-cap_inner,body_shoulder_height=shoulder,
        body_thread_centre_r=male,cap_thread_centre_r=cap_inner+p['thread_embed'],
        cap_thread_turns=cap_turns,body_thread_height=p['thread_pitch']*p['thread_turns'],
        cap_thread_height=p['thread_pitch']*cap_turns,cap_thread_z=cap_z,body_thread_z=body_z,
        thread_start_gap=p['thread_offset']-p['thread_radius'],
        thread_end_gap=p['neck_height']-p['thread_offset']-p['thread_pitch']*p['thread_turns']-p['thread_radius'],
        assembly_rotation=rotation,drain_inner_r=r1,drain_outer_r=r2,
        drain_inner_count=count(r1),drain_outer_count=count(r2),
        assembly_height=assembly,usable_length=assembly-2*p['bottom_thickness'])


def drain_centres(p):
    d=dimensions(p); centres=[(0,0)]
    for ring,phase in [('inner',0),('outer',p['drain_outer_phase'])]:
        for i in range(d['drain_'+ring+'_count']):
            angle=math.radians(phase+360*i/d['drain_'+ring+'_count'])
            r=d['drain_'+ring+'_r']; centres.append((r*math.cos(angle),r*math.sin(angle)))
    return centres


def thread_geometry(p,cap):
    d=dimensions(p); prefix='cap' if cap else 'body'
    turns=d['cap_thread_turns'] if cap else p['thread_turns']
    return dict(start=d[prefix+'_thread_z'],height=d[prefix+'_thread_height'],
        twist=360*turns,phase=p['cap_thread_phase'] if cap else 0,
        centre_r=d[prefix+'_thread_centre_r'],radius=p['thread_radius'],operation='join')


def thread_end_frame(p, cap, end):
    """Local mm frame; the tilted plane matches the user's four MoveFace edits."""
    t = thread_geometry(p, cap)
    angle = math.radians(t['phase'] + (t['twist'] if end else 0))
    radial = (math.cos(angle), math.sin(angle), 0)
    h = p['thread_pitch'] / (2 * math.pi)
    length = math.hypot(t['centre_r'], h)
    tangent = (-t['centre_r'] * math.sin(angle) / length,
               t['centre_r'] * math.cos(angle) / length, h / length)
    binormal = (h * math.sin(angle) / length, -h * math.cos(angle) / length,
                t['centre_r'] / length)
    centre = (t['centre_r'] * radial[0], t['centre_r'] * radial[1],
              t['start'] + (t['height'] if end else 0))
    key = ('cap' if cap else 'body') + ('_end' if end else '_start') + '_pivot_fraction'
    offset = (-1 if cap else 1) * p['thread_radius'] * p[key]
    pivot = tuple(c + offset * r for c, r in zip(centre, radial))
    sign = (1 if cap else -1) * (-1 if end else 1)
    tilt = math.radians(p['thread_end_tilt'])
    normal = tuple(t * math.cos(tilt) + sign * r * math.sin(tilt)
                   for t, r in zip(tangent, radial))
    return dict(centre=centre, pivot=pivot, tangent=tangent, normal=normal,
                axis=tuple(-sign * b for b in binormal), pivot_parameter=key)


def validate(p):
    def require(condition,message):
        if not condition: raise ValueError(message)
    require(all(math.isfinite(v) and v>0 for v in p.values()),'Thông số phải dương, hữu hạn.')
    d=dimensions(p)
    require(0<p['drain_outer_phase']<90,'Góc vòng lỗ phải giữa 0 và 90 deg.')
    require(0<p['cap_thread_phase']<180,'Pha ren nắp phải giữa 0 và 180 độ để ràng buộc sketch góc rõ ràng.')
    require(p['thread_end_tilt']<80,'Góc nghiêng đầu ren phải nhỏ hơn 80 độ; cần kiểm tra kernel và in thử.')
    require(all(p[name]<1 for name in UNITLESS if name.endswith('_pivot_fraction')),
            'Tỷ lệ lệch trục đầu ren phải nhỏ hơn một bán kính tiết diện.')
    require(p['neck_wall']>=1.8-1e-8 and d['neck_inner_r']>p['inside_bottom_radius'],'Cổ thân quá mỏng/nhỏ.')
    require(d['cap_wall']>=1.2,'Thành vỏ nắp quá mỏng; tăng thành thân hoặc giảm cỡ ren.')
    require(p['thread_turns']>=1 and p['thread_pitch']>4*p['thread_radius'],'Bước ren quá nhỏ hoặc dưới một vòng.')
    require(p['thread_embed']<p['thread_radius'] and p['thread_clearance']<p['thread_radius'],'Độ chìm hoặc khe hở ren quá lớn.')
    require(d['outer_r']>p['outside_bottom_radius'] and d['body_inner_r']>p['inside_bottom_radius'],'Bo đáy không vừa.')
    require(d['body_shoulder_height']>p['bottom_thickness']+p['inside_bottom_radius'],'Thân quá thấp cho vùng cổ.')
    require(p['outside_bottom_radius']<=p['bottom_thickness']+min(p['wall_thickness'],d['cap_wall']), 'Bo ngoài cắt quá sâu vào đáy mỏng.')
    require(p['neck_lip_radius']+p['mouth_inside_radius']<p['neck_wall'], 'Hai bo đầu cổ chạm nhau.')
    require(p['shoulder_radius']+p['mouth_inside_radius']<d['cap_wall'], 'Hai bo miệng nắp chạm nhau.')
    require(p['shoulder_radius']<d['outer_r']-d['neck_r'], 'Bo vai thân quá lớn.')
    require(p['neck_lip_radius']<d['thread_end_gap'], 'Bo đầu cổ chạm ren ngoài.')
    for cap in (False,True):
        t=thread_geometry(p,cap)
        floor=p['bottom_thickness']+p['inside_bottom_radius'] if cap else d['body_shoulder_height']
        lip=p['mouth_inside_radius'] if cap else p['neck_lip_radius']
        require(t['start']-t['radius']>floor and t['start']+t['height']+t['radius']<p['cap_height' if cap else 'body_height']-lip,
            'Ren vượt vùng cho phép; tăng chiều cao hoặc giảm số vòng/bước ren.')
    centres=drain_centres(p)
    for i,a in enumerate(centres):
        require(d['body_inner_r']-p['inside_bottom_radius']-math.hypot(*a)-p['bottom_drain_diameter']/2>=2.5,'Lỗ gần bo lòng.')
        for b in centres[i+1:]:
            require(math.dist(a,b)-p['bottom_drain_diameter']>=3-1e-8,'Lỗ cách nhau dưới 3 mm.')
    return d


def thread_end_face(body, location, normal, label):
    import adsk.core as core
    matches = []
    for face in body.faces:
        plane = core.Plane.cast(face.geometry)
        if not plane:
            continue
        n = (plane.normal.x, plane.normal.y, plane.normal.z)
        origin = (plane.origin.x * 10, plane.origin.y * 10, plane.origin.z * 10)
        if (abs(abs(sum(a * b for a, b in zip(n, normal))) - 1) < 1e-8 and
                abs(sum((a - b) * c for a, b, c in zip(location, origin, n))) < 0.001):
            matches.append(face)
    if len(matches) != 1:
        raise RuntimeError('{}: expected one thread end face, found {}'.format(label, len(matches)))
    return matches[0]


def build(design, p, progress):
    import adsk.core as core
    import adsk.fusion as fusion
    validate(p)
    value = core.ValueInput.createByString
    point = core.Point3D.create
    for name, number in p.items():
        units = '' if name in UNITLESS else 'deg' if name in ANGLES else 'mm'
        expression = '{} {}'.format(number, units).strip()
        design.userParameters.add(name, value(expression), units, COMMENTS[name])
    for name, (expression, units) in DERIVED.items():
        design.userParameters.add(name, value(expression), units, 'Tự tính; giữ công thức.')

    def cm(expression):
        return design.unitsManager.evaluateExpression(expression, 'mm')

    def collection(items):
        result = core.ObjectCollection.create()
        for item in items:
            result.add(item)
        return result

    def healthy(feature, name):
        feature.name = name
        if feature.healthState != fusion.FeatureHealthStates.HealthyFeatureHealthState:
            raise RuntimeError(name + ': ' + feature.errorOrWarningMessage)
        return feature

    def offset(comp, expression):
        inp = comp.constructionPlanes.createInput()
        inp.setByOffset(comp.xYConstructionPlane, value(expression))
        plane = comp.constructionPlanes.add(inp)
        plane.isLightBulbOn = False
        return plane

    def radius_dimension(sketch, circle, expression):
        c = circle.centerSketchPoint.geometry
        dim = sketch.sketchDimensions.addRadialDimension(circle, point(c.x + 0.2, c.y + 0.2, 0))
        dim.parameter.expression = expression

    def circle_at_origin(comp, plane, radius, name):
        sketch = comp.sketches.add(plane)
        sketch.name = name
        circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), cm(radius))
        sketch.geometricConstraints.addCoincident(circle.centerSketchPoint, sketch.originPoint)
        radius_dimension(sketch, circle, radius)
        return sketch

    def position(sketch, circle, expressions, basis):
        orientations = (fusion.DimensionOrientations.HorizontalDimensionOrientation,
                        fusion.DimensionOrientations.VerticalDimensionOrientation)
        for expression, axis in zip(expressions, basis):
            c = circle.centerSketchPoint.geometry
            dim = sketch.sketchDimensions.addDistanceDimension(sketch.originPoint, circle.centerSketchPoint,
                orientations[axis], point(c.x + 0.2, c.y + 0.2, 0))
            dim.parameter.expression = expression

    def extrude(comp, sketch, distance, operation, name, target=None):
        if not sketch.isFullyConstrained:
            raise RuntimeError('Sketch chưa ràng buộc đầy đủ: ' + sketch.name)
        inp = comp.features.extrudeFeatures.createInput(sketch.profiles.item(0), operation)
        inp.setOneSideExtent(fusion.DistanceExtentDefinition.create(value(distance)),
                             fusion.ExtentDirections.PositiveExtentDirection)
        if target and operation == fusion.FeatureOperations.CutFeatureOperation:
            inp.participantBodies = [target]
        result = healthy(comp.features.extrudeFeatures.add(inp), name)
        sketch.isVisible = False
        return result

    def round_edge(comp, body, z, radius, fillet, name):
        edges = []
        for edge in body.edges:
            circle = core.Circle3D.cast(edge.geometry)
            if circle and abs(circle.center.z - cm(z)) < 1e-6 and abs(circle.radius - cm(radius)) < 1e-6:
                edges.append(edge)
        if len(edges) != 1:
            raise RuntimeError('{}: expected one circular edge, found {}'.format(name, len(edges)))
        inp = comp.features.filletFeatures.createInput()
        inp.edgeSetInputs.addConstantRadiusEdgeSet(collection(edges), value(fillet), False)
        healthy(comp.features.filletFeatures.add(inp), name)

    new = fusion.FeatureOperations.NewBodyFeatureOperation
    join = fusion.FeatureOperations.JoinFeatureOperation
    cut = fusion.FeatureOperations.CutFeatureOperation
    occurrence = design.rootComponent.occurrences.addNewComponent(core.Matrix3D.create())
    comp = occurrence.component
    comp.name = 'ElectricToothbrushCase'
    # Move the completed cap aside before building the body, so Join cannot merge them.
    for cap, label in [(True, 'Cap'), (False, 'Body')]:
        progress(label + ': shell')
        height = 'cap_height' if cap else 'body_height'
        inner = 'cap_inner_r' if cap else 'body_inner_r'
        shell = circle_at_origin(comp, comp.xYConstructionPlane, 'outer_r', label + ' outside')
        body = extrude(comp, shell, height if cap else 'body_shoulder_height', new, label + ' blank').bodies.item(0)
        if not cap:
            neck = circle_at_origin(comp, offset(comp, 'body_shoulder_height'), 'neck_r', 'Body neck')
            extrude(comp, neck, 'neck_height', join, 'Neck join', body)
        bore = circle_at_origin(comp, offset(comp, 'bottom_thickness'), inner, label + ' bore')
        extrude(comp, bore, height + ' - bottom_thickness', cut, label + ' cavity', body)
        round_edge(comp, body, '0 mm', 'outer_r', 'outside_bottom_radius', label + ' outside bottom')
        round_edge(comp, body, 'bottom_thickness', 'cap_inner_r' if cap else inner, 'inside_bottom_radius', label + ' inside bottom')
        if not cap:
            round_edge(comp, body, 'body_height', 'neck_r', 'neck_lip_radius', 'Body rounded neck tip')
            round_edge(comp, body, 'body_height', 'neck_inner_r', 'mouth_inside_radius', 'Body inside tip')
            round_edge(comp, body, 'body_shoulder_height', 'outer_r', 'shoulder_radius', 'Body outer shoulder')
        else:
            round_edge(comp, body, 'cap_height', 'outer_r', 'shoulder_radius', 'Cap outer lip')
            round_edge(comp, body, 'cap_height', 'cap_inner_r', 'mouth_inside_radius', 'Cap entry round')
        prefix = 'cap' if cap else 'body'
        start = prefix + '_thread_z'
        height_expr = prefix + '_thread_height'
        centre_expr = prefix + '_thread_centre_r'
        turns_expr = 'cap_thread_turns' if cap else 'thread_turns'
        progress(label + ': constrain helix radius')
        radial = comp.sketches.add(offset(comp,start))
        radial.name = label + ' helix radius'
        phase = math.radians(p['cap_thread_phase']) if cap else 0
        ray = radial.sketchCurves.sketchLines.addByTwoPoints(radial.originPoint,
            point(cm(centre_expr)*math.cos(phase),cm(centre_expr)*math.sin(phase),0))
        if cap:
            reference = radial.sketchCurves.sketchLines.addByTwoPoints(radial.originPoint,point(0.5,0,0))
            reference.isConstruction = True
            # Constrain the finite reference segment, including both endpoints.
            radial.geometricConstraints.addHorizontal(reference)
            dim = radial.sketchDimensions.addDistanceDimension(reference.startSketchPoint,
                reference.endSketchPoint,fusion.DimensionOrientations.AlignedDimensionOrientation,
                point(0.3,-0.2,0))
            dim.parameter.expression = '5 mm'
            dim = radial.sketchDimensions.addAngularDimension(reference,ray,point(0.2,0.2,0))
            dim.parameter.expression = 'cap_thread_phase'
        else:
            radial.geometricConstraints.addHorizontal(ray)
        dim = radial.sketchDimensions.addDistanceDimension(ray.startSketchPoint,ray.endSketchPoint,
            fusion.DimensionOrientations.AlignedDimensionOrientation,point(0.5,0.2,0))
        dim.parameter.expression = centre_expr
        if not radial.isFullyConstrained:
            details = []
            for segment in radial.sketchCurves.sketchLines:
                details.append('line={}, start={}, end={}'.format(segment.isFullyConstrained,
                    segment.startSketchPoint.isFullyConstrained,segment.endSketchPoint.isFullyConstrained))
            raise RuntimeError('Unconstrained sketch: {} ({})'.format(radial.name,'; '.join(details)))

        axial = comp.sketches.add(comp.xZConstructionPlane)
        axial.name = label + ' thread axis'
        lo = axial.modelToSketchSpace(point(0, 0, cm(start)))
        hi = axial.modelToSketchSpace(point(0, 0, cm(start) + cm(height_expr)))
        line = axial.sketchCurves.sketchLines.addByTwoPoints(lo, hi)
        axis = 0 if abs(hi.x-lo.x) > abs(hi.y-lo.y) else 1
        if axis == 1:
            axial.geometricConstraints.addVertical(line)
            axial.geometricConstraints.addVerticalPoints(axial.originPoint, line.startSketchPoint)
        else:
            axial.geometricConstraints.addHorizontal(line)
            axial.geometricConstraints.addHorizontalPoints(axial.originPoint, line.startSketchPoint)
        orientation = (fusion.DimensionOrientations.HorizontalDimensionOrientation,
                       fusion.DimensionOrientations.VerticalDimensionOrientation)[axis]
        dim = axial.sketchDimensions.addDistanceDimension(axial.originPoint, line.startSketchPoint,
            orientation, point(lo.x+0.3, lo.y+0.3, 0))
        dim.parameter.expression = start
        dim = axial.sketchDimensions.addDistanceDimension(line.startSketchPoint, line.endSketchPoint,
            orientation, point(hi.x+0.3, hi.y+0.3, 0))
        dim.parameter.expression = height_expr
        if not axial.isFullyConstrained:
            raise RuntimeError('Thread axis is underconstrained: ' + label)
        path = comp.features.createPath(line, False)
        # An open radial line creates a helicoid; its longest edge is the helix.
        progress(label + ': build helix surface')
        inp = comp.features.sweepFeatures.createInput(comp.createOpenProfile(ray,False),path,new)
        inp.isSolid = False
        inp.orientation = fusion.SweepOrientationTypes.PerpendicularOrientationType
        inp.twistAngle = value(turns_expr + ' * 360 deg')
        helix = healthy(comp.features.sweepFeatures.add(inp),label + ' helix surface')
        surface = helix.bodies.item(0)
        edge = max(surface.edges,key=lambda candidate:candidate.length)
        ends = (edge.startVertex.geometry,edge.endVertex.geometry)
        expected_length = math.hypot(2*math.pi*cm(centre_expr)*thread_geometry(p,cap)['twist']/360,cm(height_expr))
        if (abs(abs(ends[1].z-ends[0].z)-cm(height_expr)) > 1e-5 or
                abs(edge.length-expected_length) > expected_length*1e-4):
            raise RuntimeError('Helix edge does not span the whole thread: ' + label)
        helix_path = comp.features.createPath(edge,False)
        plane_input = comp.constructionPlanes.createInput()
        if not plane_input.setByPath(helix_path,fusion.PathDistanceTypes.ProportionalPathDistanceType,value('0')):
            raise RuntimeError('Cannot create plane normal to helix: ' + label)
        plane = comp.constructionPlanes.add(plane_input)
        plane.isLightBulbOn = False
        thread = comp.sketches.add(plane)
        thread.name = label + ' round thread profile'
        # Project the actual path endpoint, keeping the circle attached after recompute.
        vertex = edge.endVertex if helix_path.item(0).isOpposedToEntity else edge.startVertex
        projected = thread.project2([vertex],True)
        if len(projected)!=1 or not fusion.SketchPoint.cast(projected[0]):
            raise RuntimeError('Cannot project helix endpoint: ' + label)
        centre = projected[0]
        radius_expr = 'thread_radius'
        circle = thread.sketchCurves.sketchCircles.addByCenterRadius(centre.geometry,cm(radius_expr))
        thread.geometricConstraints.addCoincident(circle.centerSketchPoint,centre)
        radius_dimension(thread,circle,radius_expr)
        progress(label + ': sweep round thread')
        inp = comp.features.sweepFeatures.createInput(thread.profiles.item(0),helix_path,join)
        inp.isSolid = True
        inp.orientation = fusion.SweepOrientationTypes.PerpendicularOrientationType
        healthy(comp.features.sweepFeatures.add(inp),label + ' round thread')
        # Recreate the four manual MoveFace edits using linked, dimensioned axes.
        for end in (False, True):
            end_label = label + (' end' if end else ' start') + ' thread tilt'
            progress(end_label)
            frame = thread_end_frame(p, cap, end)
            face = thread_end_face(body, frame['centre'], frame['tangent'], end_label)
            endpoint = max((edge.startVertex, edge.endVertex), key=lambda v:v.geometry.z) if end else min(
                (edge.startVertex, edge.endVertex), key=lambda v:v.geometry.z)
            axis_plane = plane
            if endpoint.geometry.distanceTo(vertex.geometry) > 1e-6:
                plane_input = comp.constructionPlanes.createInput()
                if not plane_input.setByPath(helix_path,
                        fusion.PathDistanceTypes.ProportionalPathDistanceType, value('1')):
                    raise RuntimeError('Cannot create end tilt plane: ' + end_label)
                axis_plane = comp.constructionPlanes.add(plane_input)
                axis_plane.isLightBulbOn = False
            axes = comp.sketches.add(axis_plane)
            axes.name = end_label + ' axis'
            linked_centre = axes.project2([endpoint], True)
            linked_z = axes.project2([comp.zConstructionAxis], True)
            if (len(linked_centre) != 1 or not fusion.SketchPoint.cast(linked_centre[0]) or
                    len(linked_z) != 1 or not fusion.SketchLine.cast(linked_z[0])):
                raise RuntimeError('Cannot project linked tilt references: ' + end_label)
            local_pivot = axes.modelToSketchSpace(point(*(x / 10 for x in frame['pivot'])))
            radial_offset = axes.sketchCurves.sketchLines.addByTwoPoints(linked_centre[0], local_pivot)
            radial_offset.isConstruction = True
            axes.geometricConstraints.addPerpendicular2(radial_offset, linked_z[0])
            dim = axes.sketchDimensions.addDistanceDimension(radial_offset.startSketchPoint,
                radial_offset.endSketchPoint, fusion.DimensionOrientations.AlignedDimensionOrientation,
                point(local_pivot.x + 0.2, local_pivot.y + 0.2, 0))
            dim.parameter.expression = 'thread_radius * ' + frame['pivot_parameter']
            axis_tip = tuple(c / 10 + a * 0.5 for c, a in zip(frame['pivot'], frame['axis']))
            rotation_axis = axes.sketchCurves.sketchLines.addByTwoPoints(radial_offset.endSketchPoint,
                axes.modelToSketchSpace(point(*axis_tip)))
            rotation_axis.isConstruction = True
            axes.geometricConstraints.addParallel(rotation_axis, linked_z[0])
            dim = axes.sketchDimensions.addDistanceDimension(rotation_axis.startSketchPoint,
                rotation_axis.endSketchPoint, fusion.DimensionOrientations.AlignedDimensionOrientation,
                point(local_pivot.x + 0.3, local_pivot.y + 0.3, 0))
            dim.parameter.expression = '5 mm'
            if not axes.isFullyConstrained:
                raise RuntimeError('Unconstrained tilt axis: ' + end_label)
            inp = comp.features.moveFeatures.createInput2(collection([face]))
            if not inp.defineAsRotate(rotation_axis, value('thread_end_tilt')):
                raise RuntimeError('Cannot define thread end rotation: ' + end_label)
            healthy(comp.features.moveFeatures.add(inp), end_label)
            thread_end_face(body, frame['pivot'], frame['normal'], end_label)
            axes.isVisible = False
        surface.name = label + ' helix helper (surface)'
        surface.isVisible = False
        for sketch in (thread,axial,radial): sketch.isVisible = False
        progress(label + ': round thread')

        if not cap:
            progress('Body: drainage')
            centre = circle_at_origin(comp, comp.xYConstructionPlane, 'bottom_drain_diameter / 2', 'Centre drain')
            extrude(comp, centre, 'bottom_thickness', cut, 'Centre drain cut', body)
            for ring, phase_expr in [('inner', '0 deg'), ('outer', 'drain_outer_phase')]:
                r = 'drain_' + ring + '_r'
                sketch = comp.sketches.add(comp.xYConstructionPlane)
                sketch.name = ring + ' drain seed'
                x, y = r + ' * cos(' + phase_expr + ')', r + ' * sin(' + phase_expr + ')'
                curve = sketch.sketchCurves.sketchCircles.addByCenterRadius(point(cm(x), cm(y), 0), cm('bottom_drain_diameter / 2'))
                if ring == 'inner':
                    sketch.geometricConstraints.addHorizontalPoints(sketch.originPoint, curve.centerSketchPoint)
                    c = curve.centerSketchPoint.geometry
                    dim = sketch.sketchDimensions.addDistanceDimension(sketch.originPoint, curve.centerSketchPoint,
                        fusion.DimensionOrientations.HorizontalDimensionOrientation, point(c.x, c.y + 0.2, 0))
                    dim.parameter.expression = r
                else:
                    position(sketch, curve, (x, y), (0, 1))
                radius_dimension(sketch, curve, 'bottom_drain_diameter / 2')
                seed = extrude(comp, sketch, 'bottom_thickness', cut, ring + ' drain cut', body)
                inp = comp.features.circularPatternFeatures.createInput(collection([seed]), comp.zConstructionAxis)
                inp.quantity = value('drain_' + ring + '_count')
                inp.totalAngle = value('360 deg')
                inp.isSymmetric = False
                inp.patternComputeOption = fusion.PatternComputeOptions.IdenticalPatternCompute
                healthy(comp.features.circularPatternFeatures.add(inp), ring + ' drainage pattern')
        else:
            inp = comp.features.moveFeatures.createInput2(collection([body]))
            inp.defineAsTranslateXYZ(value('outside_diameter + layout_gap'), value('0 mm'), value('0 mm'), False)
            healthy(comp.features.moveFeatures.add(inp), 'Cap print layout')
        body.name = label
    progress('Verify completed model')
    check_model(design)


def check_model(design):
    import adsk.core as core
    import adsk.fusion as fusion
    if not design.computeAll():
        raise RuntimeError('Fusion computeAll failed.')
    p = {name: design.userParameters.itemByName(name).value *
         (180/math.pi if name in ANGLES else 1 if name in UNITLESS else 10) for name in BASE}
    d = validate(p)
    for name, (_, units) in DERIVED.items():
        actual = design.userParameters.itemByName(name).value * (10 if units == 'mm' else 180/math.pi if units == 'deg' else 1)
        if abs(actual - d[name]) > 1e-6:
            raise RuntimeError('Derived expression mismatch: ' + name)
    if design.rootComponent.occurrences.count != 1:
        raise RuntimeError('Expected exactly one case component.')
    for i in range(design.timeline.count):
        entity = design.timeline.item(i).entity
        if isinstance(entity, fusion.Feature) and entity.healthState != fusion.FeatureHealthStates.HealthyFeatureHealthState:
            raise RuntimeError(entity.name + ': ' + entity.errorOrWarningMessage)
    comp = design.rootComponent.occurrences.item(0).component
    solids = [body for body in comp.bRepBodies if body.isSolid]
    if len(solids) != 2 or {body.name for body in solids} != {'Body', 'Cap'}:
        raise RuntimeError('Expected two printable solids named Body and Cap.')
    for sketch in comp.sketches:
        if not sketch.isFullyConstrained:
            raise RuntimeError('Unconstrained sketch: ' + sketch.name)
    if comp.features.sweepFeatures.count != 4 or comp.features.loftFeatures.count != 0:
        raise RuntimeError('Expected four sweeps and no lofts in the case component.')
    if comp.features.moveFeatures.count != 5:
        raise RuntimeError('Expected four thread face rotations and one cap layout move.')
    for label in ('Body', 'Cap'):
        body = next(body for body in solids if body.name == label)
        for end in (False, True):
            end_label = label + (' end' if end else ' start') + ' thread tilt'
            feature = comp.features.moveFeatures.itemByName(end_label)
            definition = fusion.MoveFeatureRotateDefinition.cast(feature.definition) if feature else None
            if not definition or abs(definition.angle.value - math.radians(p['thread_end_tilt'])) > 1e-8:
                raise RuntimeError('Thread end angle did not follow parameter: ' + end_label)
            frame = thread_end_frame(p, label == 'Cap', end)
            pivot = list(frame['pivot'])
            if label == 'Cap':
                pivot[0] += p['outside_diameter'] + p['layout_gap']
            thread_end_face(body, pivot, frame['normal'], end_label)
        helix_feature = comp.features.sweepFeatures.itemByName(label + ' helix surface')
        if not helix_feature or not comp.features.sweepFeatures.itemByName(label + ' round thread'):
            raise RuntimeError('Missing named helix/thread sweep: ' + label)
        twist = helix_feature.twistAngle.value
        t = thread_geometry(p, label == 'Cap')
        expected_twist = math.radians(t['twist'])
        if abs(twist - expected_twist) > 1e-6:
            raise RuntimeError('Sweep twist did not follow turns: ' + label)
        helper = helix_feature.bodies.item(0)
        helix_edge = max(helper.edges,key=lambda edge:edge.length)
        expected_length = math.hypot(2*math.pi*t['centre_r']*t['twist']/360,t['height'])
        if abs(helix_edge.length*10-expected_length) > expected_length*1e-4:
            raise RuntimeError('Helix length did not follow parameters: ' + label)
        evaluator = helix_edge.evaluator
        ok, low, high = evaluator.getParameterExtents()
        if not ok:
            raise RuntimeError('Cannot evaluate native helix: ' + label)
        for sample in range(49):
            ok, pt = evaluator.getPointAtParameter(low+(high-low)*sample/48)
            if not ok:
                raise RuntimeError('Cannot sample native helix: ' + label)
            angle = math.radians(t['phase'])+expected_twist*(pt.z*10-t['start'])/t['height']
            if math.hypot(pt.x*10-t['centre_r']*math.cos(angle),
                          pt.y*10-t['centre_r']*math.sin(angle)) > 0.01:
                raise RuntimeError('Native helix phase/hand does not match assembly formula: ' + label)
        axial = comp.sketches.itemByName(label + ' thread axis')
        line = axial.sketchCurves.sketchLines.item(0)
        start = axial.sketchToModelSpace(line.startSketchPoint.geometry)
        end = axial.sketchToModelSpace(line.endSketchPoint.geometry)
        if (math.dist((start.x*10, start.y*10, start.z*10), (0, 0, t['start'])) > 0.001 or
                math.dist((end.x*10, end.y*10, end.z*10), (0, 0, t['start'] + t['height'])) > 0.001):
            raise RuntimeError('Sweep axis did not follow thread position/height: ' + label)
        profile = comp.sketches.itemByName(label + ' round thread profile')
        circle = profile.sketchCurves.sketchCircles.item(0)
        centre = profile.sketchToModelSpace(circle.centerSketchPoint.geometry)
        if (abs(circle.radius*10-t['radius']) > 0.001 or
                abs(math.hypot(centre.x,centre.y)*10-t['centre_r']) > 0.001 or
                min(abs(centre.z*10-t['start']),abs(centre.z*10-t['start']-t['height'])) > 0.001):
            raise RuntimeError('Round profile did not follow helix/radius: ' + label)
        bounds = body.preciseBoundingBox
        expected = design.userParameters.itemByName('cap_height' if label == 'Cap' else 'body_height').value
        if abs(bounds.maxPoint.z - bounds.minPoint.z - expected) > 0.001:
            raise RuntimeError(label + ': unexpected height.')
        if abs((bounds.maxPoint.y - bounds.minPoint.y) * 10 - p['outside_diameter']) > 0.01:
            raise RuntimeError(label + ': unexpected diameter.')
        if label == 'Cap':
            centre_x = (bounds.maxPoint.x + bounds.minPoint.x) * 5
            if abs(centre_x - p['outside_diameter'] - p['layout_gap']) > 0.01:
                raise RuntimeError('Cap layout did not follow diameter.')
        else:
            for ring in ('inner', 'outer'):
                pattern = comp.features.circularPatternFeatures.itemByName(ring + ' drainage pattern')
                if round(pattern.quantity.value) != d['drain_' + ring + '_count']:
                    raise RuntimeError('Drain count did not follow parameters: ' + ring)
        # Check actual void and wall, after the cap's parametric print-layout move.
        cap = label == 'Cap'
        layout_x = p['outside_diameter']+p['layout_gap'] if cap else 0
        main_r = d['cap_inner_r' if cap else 'body_inner_r']
        main_top = t['start']-t['radius'] if cap else d['body_shoulder_height']
        main_z = (p['bottom_thickness']+p['inside_bottom_radius']+main_top)/2
        local_r = d['cap_inner_r' if cap else 'neck_inner_r']
        local_z = p['cap_height']-p['mouth_inside_radius']/2 if cap else p['body_height']-p['neck_lip_radius']/2
        for radius,z,inside in ((main_r-0.05,main_z,False),
                                ((main_r+d['outer_r'])/2,main_z,True),
                                (local_r-0.05,local_z,False)):
            result = body.pointContainment(core.Point3D.create((layout_x+radius)/10,0,z/10))
            expected = (fusion.PointContainment.PointInsidePointContainment if inside else
                        fusion.PointContainment.PointOutsidePointContainment)
            if result != expected:
                raise RuntimeError('Native cavity/wall does not match parameters: ' + label)


def verify_variants(design):
    params = design.userParameters
    original = {name: params.itemByName(name).expression for name in BASE}
    cases = [dict(body_height=240, cap_height=100), dict(outside_diameter=60),
             dict(body_height=31.6, cap_height=24),
             dict(thread_turns=1.8,drain_outer_phase=20),
             dict(thread_pitch=4.5,thread_radius=0.85,thread_clearance=0.25),
             dict(bottom_drain_diameter=3.5),
             dict(thread_end_tilt=60,body_end_pivot_fraction=0.4,cap_end_pivot_fraction=0.5),
             dict(cap_thread_phase=120,cap_extra_turns=0.6,cap_thread_offset=0.5)]
    try:
        for changes in cases:
            for name, expression in original.items():
                params.itemByName(name).expression = expression
            for name, number in changes.items():
                units = 'deg' if name in ANGLES else '' if name in UNITLESS else 'mm'
                params.itemByName(name).expression = '{} {}'.format(number, units).strip()
            p = {name: params.itemByName(name).value * (180/math.pi if name in ANGLES else 1 if name in UNITLESS else 10) for name in BASE}
            validate(p)
            check_model(design)
    finally:
        for name, expression in original.items():
            params.itemByName(name).expression = expression
        check_model(design)


def run(context):
    import adsk.core as core
    import adsk.fusion as fusion
    app = core.Application.get()
    stage = 'Validate parameters'
    def progress(message):
        nonlocal stage
        stage = message
        app.log(message)
        adsk.doEvents()
    import adsk
    try:
        p = defaults(SHORT_TEST)
        validate(p)
        doc = app.documents.add(core.DocumentTypes.FusionDesignDocumentType)
        doc.name = 'Electric toothbrush case - parametric'
        design = fusion.Design.cast(app.activeProduct)
        design.designType = fusion.DesignTypes.ParametricDesignType
        design.unitsManager.distanceDisplayUnits = fusion.DistanceUnits.MillimeterDistanceUnits
        build(design, p, progress)
        if VERIFY_VARIANTS:
            progress('Verify parameter changes')
            verify_variants(design)
        app.activeViewport.fit()
        app.userInterface.messageBox('Đã tạo thân và nắp. Sửa tại Modify > Change Parameters.\n'
            'Ren tròn ngoài trên thân, ren trong ở nắp; cần in thử độ vừa.\n'
            'Chế độ kiểm tra biến thể: ' + str(VERIFY_VARIANTS))
    except Exception:
        details = 'FAILED at: ' + stage + '\n' + traceback.format_exc()
        app.log(details)
        app.userInterface.messageBox(details)
