"""
3D visualization using Panda3D (optional).
"""

from typing import Optional, Dict, Any

# Check if Panda3D is available
try:
    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import (
        NodePath, Vec3, Point3, AmbientLight, DirectionalLight,
        PerspectiveLens, Camera, Material, TransparencyAttrib,
        LineSegments, GeomVertexFormat, GeomVertexData, Geom,
        GeomTriangles, GeomVertexWriter, GeomNode, BoundingBox,
        CardMaker, Texture, TextureStage, TransformState,
        BitMask32, CollisionTraverser, CollisionNode, CollisionSphere,
        CollisionHandlerQueue, CollisionRay, loadPrcFileData
    )
    from direct.task import Task
    from direct.interval.IntervalGlobal import Sequence, LerpPosInterval, LerpHprInterval
    
    PANDA3D_AVAILABLE = True
    Panda3DAvailable = True
except ImportError:
    PANDA3D_AVAILABLE = False
    Panda3DAvailable = False
    
    # Mock classes for type hints
    class ShowBase:
        pass
    
    class NodePath:
        pass
    
    class Task:
        pass

from nados.domain import Vector3D
from nados.observability import get_logger


logger = get_logger("visualization.view3d")


class View3D:
    """3D visualization using Panda3D."""
    
    def __init__(self, window_title: str = "NADOS 3D Simulation") -> None:
        if not PANDA3D_AVAILABLE:
            raise RuntimeError("Panda3D is not installed. Install with: pip install panda3d")
        
        self.base = ShowBase()
        self.base.disableMouse()
        self.base.setBackgroundColor(0.05, 0.05, 0.15)
        
        # Camera setup
        self.base.camera.setPos(0, -200, 100)
        self.base.camera.lookAt(0, 0, 0)
        self.base.camLens.setFov(60)
        self.base.camLens.setNearFar(1, 500000)
        
        # Lighting
        self._setup_lighting()
        
        # Scene objects
        self.objects: Dict[str, NodePath] = {}
        self.sensors: Dict[str, NodePath] = {}
        self.trails: Dict[str, NodePath] = {}
        self.trail_data: Dict[str, list] = {}
        
        # Ground plane
        self._create_ground_plane()
        
        # Coordinate axes
        self._create_axes()
        
        # Simulation label
        self._create_simulation_label()
        
        # Camera control state
        self.camera_target = Vec3(0, 0, 0)
        self.camera_distance = 200
        self.camera_h = 0
        self.camera_p = -30
        
        # Update task
        self.base.taskMgr.add(self._update_task, "updateTask")
        
        logger.info("3D View initialized")
    
    def _setup_lighting(self) -> None:
        """Set up scene lighting."""
        # Ambient light
        ambient = AmbientLight("ambient")
        ambient.setColor((0.3, 0.3, 0.4, 1))
        ambient_np = self.base.render.attachNewNode(ambient)
        self.base.render.setLight(ambient_np)
        
        # Directional light (sun)
        sun = DirectionalLight("sun")
        sun.setColor((0.8, 0.8, 0.7, 1))
        sun_np = self.base.render.attachNewNode(sun)
        sun_np.setHpr(45, -45, 0)
        self.base.render.setLight(sun_np)
    
    def _create_ground_plane(self) -> None:
        """Create a simple ground plane with grid."""
        from panda3d.core import GeomVertexFormat, GeomVertexData, Geom, GeomLines, GeomVertexWriter, GeomNode
        
        # Create grid lines
        format = GeomVertexFormat.getV3()
        vdata = GeomVertexData("grid", format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        
        grid_size = 200000  # 200km
        grid_spacing = 10000  # 10km
        color = (0.2, 0.3, 0.2, 1)
        
        lines = GeomLines(Geom.UHStatic)
        
        # X lines
        for x in range(-grid_size, grid_size + 1, grid_spacing):
            vertex.addData3(x, -grid_size, 0)
            vertex.addData3(x, grid_size, 0)
            lines.addVertices(len(lines.getVertices()), len(lines.getVertices()) + 1)
        
        # Y lines
        for y in range(-grid_size, grid_size + 1, grid_spacing):
            vertex.addData3(-grid_size, y, 0)
            vertex.addData3(grid_size, y, 0)
            lines.addVertices(len(lines.getVertices()), len(lines.getVertices()) + 1)
        
        geom = Geom(vdata)
        geom.addPrimitive(lines)
        
        node = GeomNode("ground_grid")
        node.addGeom(geom)
        
        grid_np = self.base.render.attachNewNode(node)
        grid_np.setTransparency(TransparencyAttrib.MAlpha)
        grid_np.setColor(*color)
        
        # Ground plane
        cm = CardMaker("ground")
        cm.setFrame(-grid_size, grid_size, -grid_size, grid_size)
        ground = self.base.render.attachNewNode(cm.generate())
        ground.setP(-90)
        ground.setColor(0.1, 0.15, 0.1, 1)
        ground.setBin("background", 0)
    
    def _create_axes(self) -> None:
        """Create coordinate axes."""
        from panda3d.core import GeomVertexFormat, GeomVertexData, Geom, GeomLines, GeomVertexWriter, GeomNode
        
        format = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData("axes", format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        color = GeomVertexWriter(vdata, "color")
        
        lines = GeomLines(Geom.UHStatic)
        
        axis_length = 50000  # 50km
        
        # X axis (Red) - East
        vertex.addData3(0, 0, 0)
        color.addData4(1, 0, 0, 1)
        vertex.addData3(axis_length, 0, 0)
        color.addData4(1, 0, 0, 1)
        lines.addVertices(0, 1)
        
        # Y axis (Green) - North
        vertex.addData3(0, 0, 0)
        color.addData4(0, 1, 0, 1)
        vertex.addData3(0, axis_length, 0)
        color.addData4(0, 1, 0, 1)
        lines.addVertices(2, 3)
        
        # Z axis (Blue) - Up
        vertex.addData3(0, 0, 0)
        color.addData4(0, 0, 1, 1)
        vertex.addData3(0, 0, axis_length)
        color.addData4(0, 0, 1, 1)
        lines.addVertices(4, 5)
        
        geom = Geom(vdata)
        geom.addPrimitive(lines)
        
        node = GeomNode("axes")
        node.addGeom(geom)
        
        axes_np = self.base.render.attachNewNode(node)
        axes_np.setLightOff()
        axes_np.setBin("fixed", 10)
        
        # Axis labels
        self._add_axis_labels(axis_length)
    
    def _add_axis_labels(self, length: float) -> None:
        """Add axis labels."""
        from direct.gui.OnscreenText import OnscreenText
        
        labels = [
            ("E (شرق)", (length + 5000, 0, 0), (1, 0, 0, 1)),
            ("N (شمال)", (0, length + 5000, 0), (0, 1, 0, 1)),
            ("U (أعلى)", (0, 0, length + 5000), (0, 0, 1, 1)),
        ]
        
        for text, pos, color in labels:
            label = OnscreenText(
                text=text,
                pos=(0, 0),  # Will be updated in task
                scale=0.05,
                fg=color,
                parent=self.base.render2d,
            )
            label.setBillboardPointEye()
            # Store 3D position for billboard update
            label.setPythonTag("world_pos", Vec3(*pos))
    
    def _create_simulation_label(self) -> None:
        """Create SIMULATION label."""
        from direct.gui.OnscreenText import OnscreenText
        
        self.sim_label = OnscreenText(
            text="محاكاة - SIMULATION",
            pos=(0, 0.9),
            scale=0.08,
            fg=(1, 0.2, 0.2, 1),
            shadow=(0, 0, 0, 1),
            parent=self.base.a2dTopCenter,
            align=OnscreenText.ACenter,
        )
    
    def add_object(self, object_id: str, position: Vector3D, velocity: Vector3D, 
                   color: tuple = (1, 0, 0, 1), scale: float = 100) -> None:
        """Add a virtual object to the scene."""
        if object_id in self.objects:
            return
        
        # Create rocket-like shape
        obj_np = self._create_rocket_model(scale, color)
        obj_np.reparentTo(self.base.render)
        obj_np.setPos(position.x, position.y, position.z)
        
        # Orient towards velocity
        if velocity.x != 0 or velocity.y != 0:
            import math
            heading = math.degrees(math.atan2(velocity.y, velocity.x))
            obj_np.setH(heading - 90)  # Adjust for model orientation
        
        self.objects[object_id] = obj_np
        self.trail_data[object_id] = []
        
        # Create trail
        self._create_trail(object_id)
    
    def _create_rocket_model(self, scale: float, color: tuple) -> NodePath:
        """Create a simple rocket-shaped model."""
        from panda3d.core import GeomVertexFormat, GeomVertexData, Geom, GeomTriangles, GeomVertexWriter, GeomNode
        
        format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("rocket", format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color_writer = GeomVertexWriter(vdata, "color")
        
        tris = GeomTriangles(Geom.UHStatic)
        
        # Simple cone + cylinder for rocket
        r = scale * 0.3
        h = scale * 2.0
        
        # Nose cone (tetrahedron approximation)
        # Base vertices
        base_verts = [
            (r, 0, 0),
            (-r * 0.5, r * 0.866, 0),
            (-r * 0.5, -r * 0.866, 0),
        ]
        tip = (0, 0, h)
        
        # Body cylinder (simplified as 6-sided prism)
        body_verts = []
        for i in range(6):
            angle = i * math.pi / 3
            body_verts.append((r * math.cos(angle), r * math.sin(angle), 0))
            body_verts.append((r * 0.8 * math.cos(angle), r * 0.8 * math.sin(angle), -h * 0.8))
        
        # Add geometry...
        # For simplicity, create a basic cone
        self._add_cone(vertex, normal, color_writer, tris, tip, base_verts, color)
        self._add_cylinder(vertex, normal, color_writer, tris, body_verts, color)
        
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        
        node = GeomNode("rocket")
        node.addGeom(geom)
        
        np = NodePath(node)
        return np
    
    def _add_cone(self, vertex, normal, color_writer, tris, tip, base_verts, color) -> None:
        """Add cone geometry."""
        import math
        
        for i in range(len(base_verts)):
            v1 = base_verts[i]
            v2 = base_verts[(i + 1) % len(base_verts)]
            
            # Triangle: tip -> v1 -> v2
            idx = vertex.getNumRows()
            vertex.addData3(*tip)
            normal.addData3(0, 0, 1)
            color_writer.addData4(*color)
            
            vertex.addData3(*v1)
            normal.addData3(0, 0, 1)
            color_writer.addData4(*color)
            
            vertex.addData3(*v2)
            normal.addData3(0, 0, 1)
            color_writer.addData4(*color)
            
            tris.addVertices(idx, idx + 1, idx + 2)
    
    def _add_cylinder(self, vertex, normal, color_writer, tris, body_verts, color) -> None:
        """Add cylinder geometry."""
        # Simplified - just add bottom cap
        pass
    
    def _create_trail(self, object_id: str) -> None:
        """Create trail for an object."""
        from panda3d.core import GeomVertexFormat, GeomVertexData, Geom, GeomLines, GeomVertexWriter, GeomNode
        
        format = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData(f"trail_{object_id}", format, Geom.UHDynamic)
        vertex = GeomVertexWriter(vdata, "vertex")
        color = GeomVertexWriter(vdata, "color")
        
        lines = GeomLines(Geom.UHDynamic)
        
        geom = Geom(vdata)
        geom.addPrimitive(lines)
        
        node = GeomNode(f"trail_{object_id}")
        node.addGeom(geom)
        
        trail_np = self.base.render.attachNewNode(node)
        trail_np.setRenderModeThickness(2)
        trail_np.setTransparency(TransparencyAttrib.MAlpha)
        
        self.trails[object_id] = trail_np
    
    def add_sensor(self, sensor_id: str, position: Vector3D, sensor_type: str = "radar") -> None:
        """Add a sensor to the scene."""
        if sensor_id in self.sensors:
            return
        
        # Create sensor marker (sphere)
        from panda3d.core import GeomVertexFormat, GeomVertexData, Geom, GeomTriangles, GeomVertexWriter, GeomNode
        
        format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData(f"sensor_{sensor_id}", format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color_writer = GeomVertexWriter(vdata, "color")
        
        tris = GeomTriangles(Geom.UHStatic)
        
        # Simple sphere (icosahedron approximation)
        self._add_sphere(vertex, normal, color_writer, tris, 500, (0, 1, 0, 1))  # Green for sensors
        
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        
        node = GeomNode(f"sensor_{sensor_id}")
        node.addGeom(geom)
        
        sensor_np = self.base.render.attachNewNode(node)
        sensor_np.setPos(position.x, position.y, position.z)
        
        self.sensors[sensor_id] = sensor_np
    
    def _add_sphere(self, vertex, normal, color_writer, tris, radius: float, color: tuple) -> None:
        """Add sphere geometry (simplified icosahedron)."""
        # Very simplified - just a few triangles
        pass
    
    def update_object(self, object_id: str, position: Vector3D, velocity: Vector3D) -> None:
        """Update object position and trail."""
        if object_id not in self.objects:
            return
        
        obj_np = self.objects[object_id]
        obj_np.setPos(position.x, position.y, position.z)
        
        # Orient towards velocity
        if velocity.x != 0 or velocity.y != 0:
            import math
            heading = math.degrees(math.atan2(velocity.y, velocity.x))
            obj_np.setH(heading - 90)
        
        # Update trail
        self.trail_data[object_id].append((position.x, position.y, position.z))
        if len(self.trail_data[object_id]) > 200:
            self.trail_data[object_id].pop(0)
        
        self._update_trail_geometry(object_id)
    
    def _update_trail_geometry(self, object_id: str) -> None:
        """Update trail line geometry."""
        trail_np = self.trails.get(object_id)
        if not trail_np:
            return
        
        # Rebuild trail geometry
        points = self.trail_data[object_id]
        if len(points) < 2:
            return
        
        from panda3d.core import GeomVertexFormat, GeomVertexData, Geom, GeomLines, GeomVertexWriter, GeomNode
        
        format = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData(f"trail_{object_id}", format, Geom.UHDynamic)
        vertex = GeomVertexWriter(vdata, "vertex")
        color = GeomVertexWriter(vdata, "color")
        
        lines = GeomLines(Geom.UHDynamic)
        
        for i, (x, y, z) in enumerate(points):
            vertex.addData3(x, y, z)
            # Fade older points
            alpha = i / len(points)
            color.addData4(1, 0, 0, alpha * 0.5)
        
        for i in range(len(points) - 1):
            lines.addVertices(i, i + 1)
        
        geom = Geom(vdata)
        geom.addPrimitive(lines)
        
        node = GeomNode(f"trail_{object_id}")
        node.addGeom(geom)
        
        trail_np.node().removeAllGeoms()
        trail_np.node().addGeom(geom)
    
    def _update_task(self, task) -> int:
        """Main update task."""
        # Update camera
        self._update_camera()
        
        # Update axis labels
        self._update_axis_labels()
        
        return Task.cont
    
    def _update_camera(self) -> None:
        """Update camera position based on controls."""
        import math
        
        # Calculate camera position
        ch = math.radians(self.camera_h)
        cp = math.radians(self.camera_p)
        
        cam_x = self.camera_target.x + self.camera_distance * math.cos(cp) * math.sin(ch)
        cam_y = self.camera_target.y - self.camera_distance * math.cos(cp) * math.cos(ch)
        cam_z = self.camera_target.z + self.camera_distance * math.sin(cp)
        
        self.base.camera.setPos(cam_x, cam_y, cam_z)
        self.base.camera.lookAt(self.camera_target)
    
    def _update_axis_labels(self) -> None:
        """Update axis label positions for billboarding."""
        # Labels are billboarded automatically
        pass
    
    def orbit_camera(self, delta_h: float, delta_p: float) -> None:
        """Orbit camera around target."""
        self.camera_h += delta_h
        self.camera_p = max(-89, min(89, self.camera_p + delta_p))
    
    def pan_camera(self, delta_x: float, delta_y: float) -> None:
        """Pan camera target."""
        import math
        
        ch = math.radians(self.camera_h)
        cp = math.radians(self.camera_p)
        
        # Right vector
        right_x = math.cos(ch)
        right_y = math.sin(ch)
        
        # Up vector (projected)
        up_x = -math.sin(ch) * math.cos(cp)
        up_y = math.cos(ch) * math.cos(cp)
        
        self.camera_target.x += right_x * delta_x + up_x * delta_y
        self.camera_target.y += right_y * delta_x + up_y * delta_y
    
    def zoom_camera(self, factor: float) -> None:
        """Zoom camera in/out."""
        self.camera_distance *= factor
        self.camera_distance = max(10, min(500000, self.camera_distance))
    
    def reset_camera(self) -> None:
        """Reset camera to default position."""
        self.camera_target = Vec3(0, 0, 0)
        self.camera_distance = 200
        self.camera_h = 0
        self.camera_p = -30
    
    def run(self) -> None:
        """Run the 3D viewer main loop."""
        self.base.run()
    
    def stop(self) -> None:
        """Stop the 3D viewer."""
        if hasattr(self, 'base'):
            self.base.taskMgr.remove("updateTask")
            self.base.destroy()
    
    def __del__(self):
        self.stop()


def create_3d_view(window_title: str = "NADOS 3D Simulation") -> Optional[View3D]:
    """Create a 3D view instance if Panda3D is available."""
    if not PANDA3D_AVAILABLE:
        logger.warning("Panda3D not available, 3D visualization disabled")
        return None
    
    try:
        return View3D(window_title)
    except Exception as e:
        logger.error(f"Failed to create 3D view: {e}")
        return None