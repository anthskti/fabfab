"""
/services/obj_service.py - OBJ file parsing and manipulation.
    parse, manipulate, and re-export Wavefront .obj file content
"""

import re
import numpy as np
from typing import List, Dict, Tuple, Any

class OBJModel:
    """Represents a parsed .obj file with manipulation capabilities"""
    
    def __init__(self, obj_content: str):
        """Parse OBJ content into structured data"""
        self.vertices: List[np.ndarray] = []
        self.normals: List[np.ndarray] = []
        self.tex_coords: List[Tuple[float, float]] = []
        self.faces: List[List[Tuple[int, int, int]]] = []
        self.groups: Dict[str, List[int]] = {}  # Group name -> vertex indices
        self.materials: List[str] = []
        self.current_group: str = "default"
        self.lines: List[str] = []  # Store original lines for reconstruction
        
        self._parse(obj_content)
    
    def _parse(self, content: str):
        """Parse OBJ file content."""
        current_material = None
        vertex_count = 0

        for line in content.split('\n'):
            self.lines.append(line)
            line = line.strip()
            
            if not line or line.startswith('#'): # Check for group markers in comments
                if line.startswith('# GROUP:'):
                    self.current_group = line.split(':')[1].strip()
                    if self.current_group not in self.groups:
                        self.groups[self.current_group] = []
                continue
            
            parts = line.split()
            if not parts:
                continue
            
            cmd = parts[0]
            
            if cmd == 'v': # Vertex position
                vertex = np.array([float(parts[1]), float(parts[2]), float(parts[3])]) # x, y, x
                self.vertices.append(vertex)
                vertex_count += 1
                
                # Track vertex in current group
                if self.current_group not in self.groups:
                    self.groups[self.current_group] = []
                self.groups[self.current_group].append(vertex_count - 1)
                
            elif cmd == 'vn': # Vertex normal
                normal = np.array([float(parts[1]), float(parts[2]), float(parts[3])])
                self.normals.append(normal)
                
            elif cmd == 'vt': # Texture coordinate
                self.tex_coords.append((float(parts[1]), float(parts[2])))
                
            elif cmd == 'f': # Face definition
                face = []
                for vert_data in parts[1:]:
                    indices = vert_data.split('/')
                    v_idx = int(indices[0]) - 1 if indices[0] else 0
                    vt_idx = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else -1
                    vn_idx = int(indices[2]) - 1 if len(indices) > 2 and indices[2] else -1
                    face.append((v_idx, vt_idx, vn_idx))
                self.faces.append(face)
                
            elif cmd == 'usemtl': # Material usage
                if len(parts) > 1:
                    current_material = parts[1]
                    self.materials.append(current_material)

    def apply_overall_scale(self, scale: float):
        """Scale all vertices uniformly, file sizing adjustment"""
        for i in range(len(self.vertices)):
            self.vertices[i] *= scale
    
    def apply_group_scale(self, group_name: str, scale: float):
        """Scale vertices in a specific group"""
        if group_name not in self.groups:
            print(f"Warning: Group '{group_name}' not found")
            return
        
        # Calculate centroid of the group
        group_verts = [self.vertices[i] for i in self.groups[group_name]]
        if not group_verts:
            return
        
        centroid = np.mean(group_verts, axis=0)
        
        # Scale around centroid
        for idx in self.groups[group_name]:
            offset = self.vertices[idx] - centroid
            self.vertices[idx] = centroid + offset * scale

    def remove_group(self, group_name: str):
        """Remove all vertices and faces associated with a group"""
        if group_name not in self.groups:
            return
        
        # Get indices to remove
        remove_indices = set(self.groups[group_name])
        
        # Remove vertices (mark as None)
        for idx in remove_indices:
            self.vertices[idx] = None
        
        # Remove faces that reference removed vertices
        self.faces = [
            face for face in self.faces
            if not any(v_idx in remove_indices for v_idx, _, _ in face)
        ]
        
        # Remove from groups
        del self.groups[group_name]


    def smooth_normals(self, factor: float):
        """Smooth vertex normals (0.0 = original, 1.0 = fully smooth)"""
        if not self.normals or factor <= 0:
            return
        
        # Build vertex to faces mapping
        vertex_faces: Dict[int, List[int]] = {}
        for face_idx, face in enumerate(self.faces):
            for v_idx, _, _ in face:
                if v_idx not in vertex_faces:
                    vertex_faces[v_idx] = []
                vertex_faces[v_idx].append(face_idx)
        
        # Calculate smoothed normals
        smoothed_normals = []
        for i, normal in enumerate(self.normals):
            # Average with neighboring face normals
            avg_normal = normal.copy()
            
            # Find all faces using this normal
            count = 1
            for v_idx in vertex_faces:
                for face_idx in vertex_faces[v_idx]:
                    face = self.faces[face_idx]
                    for _, _, n_idx in face:
                        if n_idx == i and n_idx < len(self.normals):
                            # Average in nearby normals
                            for _, _, other_n_idx in face:
                                if other_n_idx != n_idx and other_n_idx < len(self.normals):
                                    avg_normal += self.normals[other_n_idx]
                                    count += 1
            
            avg_normal /= count
            avg_normal /= np.linalg.norm(avg_normal)  # Normalize
            
            # Blend between original and smoothed
            blended = (1 - factor) * normal + factor * avg_normal
            blended /= np.linalg.norm(blended)
            smoothed_normals.append(blended)
        
        self.normals = smoothed_normals
    
    def to_obj_string(self) -> str:
        """Export back to .obj format"""
        lines = []
        lines.append("# Generated by Procedural 3D Generator")
        lines.append("o GeneratedModel")
        lines.append("")
        
        # Write vertices by group
        vertex_remap = {}  # Old index -> new index
        new_idx = 1
        
        for group_name, indices in self.groups.items():
            lines.append(f"# GROUP:{group_name}")
            for old_idx in indices:
                if self.vertices[old_idx] is not None:
                    v = self.vertices[old_idx]
                    lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
                    vertex_remap[old_idx] = new_idx
                    new_idx += 1
        
        lines.append("")
        
        # Write normals
        for n in self.normals:
            lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
        
        lines.append("")
        
        # Write texture coordinates
        for vt in self.tex_coords:
            lines.append(f"vt {vt[0]:.6f} {vt[1]:.6f}")
        
        lines.append("")
        
        # Write faces
        for face in self.faces:
            face_str = "f"
            for v_idx, vt_idx, vn_idx in face:
                # Remap vertex index
                if v_idx not in vertex_remap:
                    continue  # Skip if vertex was removed
                
                new_v_idx = vertex_remap[v_idx]
                
                if vt_idx >= 0 and vn_idx >= 0:
                    face_str += f" {new_v_idx}/{vt_idx + 1}/{vn_idx + 1}"
                elif vn_idx >= 0:
                    face_str += f" {new_v_idx}//{vn_idx + 1}"
                elif vt_idx >= 0:
                    face_str += f" {new_v_idx}/{vt_idx + 1}"
                else:
                    face_str += f" {new_v_idx}"
            
            if len(face_str.split()) > 3:  # Only add if face has at least 3 vertices
                lines.append(face_str)
        
        return '\n'.join(lines)
    

class OBJService:
    """Service for OBJ file operations"""
    @staticmethod
    def apply_modifiers(obj_content: str, modifiers: Dict[str, Any]) -> str:
        """
        Apply modifiers to OBJ content
        
        Args:
            obj_content: Original .obj file content
            modifiers: Dictionary of modifier values
            
        Returns: Modified .obj file content
        """
        try:
            model = OBJModel(obj_content)
            
            # Apply each modifier
            for modifier_name, value in modifiers.items():
                if modifier_name == "overall_size":
                    model.apply_overall_scale(float(value))
                
                elif modifier_name.endswith("_size") and modifier_name != "overall_size":
                    # Extract group name (e.g., "leaf_size" -> "leaf")
                    group_name = modifier_name.replace("_size", "")
                    model.apply_group_scale(group_name, float(value))
                
                elif modifier_name == "smoothness":
                    # Convert 0-100 to 0.0-1.0
                    smooth_factor = float(value) / 100.0
                    model.smooth_normals(smooth_factor)
                
                elif modifier_name == "seedless" and value is True:
                    model.remove_group("seed")
                
                elif isinstance(value, bool):
                    # Generic boolean: if False, remove the group
                    if not value:
                        group_name = modifier_name.replace("_visible", "").replace("has_", "")
                        model.remove_group(group_name)
            
            return model.to_obj_string()
            
        except Exception as e:
            print(f"Error applying modifiers: {e}")
            return obj_content  # Return original on error
        
    @staticmethod
    def validate_obj(obj_content: str) -> Tuple[bool, str]:
        """
        Validate OBJ file structure
        
        Returns:
            (is_valid, error_message)
        """
        try:
            if not obj_content.strip():
                return False, "OBJ content is empty"
            
            has_vertices = "v " in obj_content
            has_faces = "f " in obj_content
            
            if not has_vertices:
                return False, "No vertices found"
            
            if not has_faces:
                return False, "No faces found"
            
            # Basic syntax check
            for line in obj_content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if not parts:
                    continue
                
                cmd = parts[0]
                if cmd == 'v' and len(parts) != 4:
                    return False, f"Invalid vertex definition: {line}"
                elif cmd == 'vn' and len(parts) != 4:
                    return False, f"Invalid normal definition: {line}"
            
            return True, "Valid OBJ file"
            
        except Exception as e:
            return False, str(e)
    