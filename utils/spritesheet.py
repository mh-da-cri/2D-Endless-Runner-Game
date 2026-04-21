import pygame

class SpriteSheet:
    def __init__(self, image):
        self.sheet = image

    def get_image(self, frame_x_index, frame_y_index, width, height, scale, colorkey=(0,0,0)):
        """
        Cắt 1 khung ảnh từ tọa độ lưới (frame_x_index, frame_y_index).
        VD: frame_x_index = 0, frame_y_index = 0 là ô đầu tiên góc trên cùng bên trái.
        """
        image = pygame.Surface((width, height)).convert_alpha()
        # Để xoá nền đen của Surface, điền background trong suốt trước
        image.fill((0,0,0,0))
        
        # Cắt hình từ sheet
        image.blit(self.sheet, (0, 0), ((frame_x_index * width), (frame_y_index * height), width, height))
        
        if scale != 1:
            image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
            
        # Lọc nền nếu không phải transparent mặc định (thường sprite cũ dùng nền lục/xanh dương/đôi khi đen)
        # Nếu ảnh gốc là có nền trong suốt (alpha channel) sẵn, ta vẫn set_colorkey cho an toàn
        image.set_colorkey(colorkey)
        
        return image

    def get_image_at(self, x, y, width, height, scale, colorkey=(0,0,0)):
        """
        Cắt 1 khung ảnh từ tọa độ pixel cứng [x, y].
        """
        image = pygame.Surface((width, height)).convert_alpha()
        image.fill((0,0,0,0))
        
        image.blit(self.sheet, (0, 0), (x, y, width, height))
        
        if scale != 1:
            image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
            
        image.set_colorkey(colorkey)
        return image
