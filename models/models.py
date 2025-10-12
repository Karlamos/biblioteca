# -*- coding: utf-8 -*-

from odoo import models, fields, api

class biblioteca_libro(models.Model):
    _name = 'biblioteca.libro'
    _description = 'biblioteca.biblioteca'
    _rec_name= 'name'

    name = fields.Char(string='Título', required=True)
    autor = fields.Many2one('biblioteca.autor', string= 'Autor',required=True)
    genero =fields.Selection([
        ('ciencia_ficcion','Ciencia Ficción'),
        ('aventura','Aventura'),
        ('romance','Romance'),
        ('fantacia','Fantacia'),
        ('historica','Historica'),
        ('filosofico','Filosófico'),
        ('politico','Político'),
        ('academico','Académica'),
        ('tragedia','Tragedia'),
        ('comedia','Comedia'),
        ('farsa','Farsa'),

    ], string='Género', required=True)
    anio_pub=fields.Char(string='Año de publicaión', required=True)

#    @api.depends('value')
 #   def _value_pc(self):
  #      for record in self:
   #          record.value2 = float(record.value) / 100


class biblioteca_Autor(models.Model):
    _name ='biblioteca.autor'
    _description = 'biblioteca.autor'
    _rec_name = 'autor'
    
    autor = fields.Char()
    descripcion = fields.Char()
    
    @api.depends('autor', 'descripcion')
    def _compute_display_name(self):
        for record in self:
            record.display_name =f"{record.autor} - {record.descripcion}"
            
class biblioteca_Editorial(models.Model):
    _name ='biblioteca.editorial'
    _description = 'biblioteca.editorial'
    _rec_name = 'firstname'
    
    firstname = fields.Char()
    lastname = fields.Char()
    
    @api.depends('firstname', 'lastname')
    def _compute_display_name(self):
        for record in self:
            record.display_name =f"{record.firstname} - {record.lastname}"
            
            
class biblioteca_Personal(models.Model):
    _name ='biblioteca.personal'
    _description = 'biblioteca.personal'
    _rec_name = 'codigo_empleado'
    
    codigo_empleado = fields.Char(string='ID Empleado', required=True)
    nombre = fields.Char(string='Nombre', required=True)
    cargo =fields.Selection([
        ('director_biblioteca','Director de biblioteca'),
        ('jefe_area','Jefe de área'),
        ('tecnico_coleccion','Técnico de colección'),
        ('tecnico_servicios','Técnico responsable de servicios a los usuarios'),
        ('tecnico_biblioteca','Técnico de biblioteca'),
        ('tecnico_tecnologias','Técnico responsable de tecnoligías de la información'),
        ('director_red','Director de red de bibliotecas'),
        ('bibliotecario','Bibliotecario'),
    ], string='Cargo', required=True)
    turno =fields.Selection([
        ('diurno','Diurno'),
        ('nocturno','Nocturno'),
        ('mixto','Mixto'),
    ], string='Turno', required=True)
    emailper = fields.Char(string='Email', required=True)
    
 #   @api.depends('nombre', 'cargo')
  #  def _compute_display_name(self):
   #     for record in self:
    #        record.display_name =f"{record.firstname} - {record.lastname}"
            
            
            
class biblioteca_Usuario(models.Model):
    _name ='biblioteca.usuario'
    _description = 'biblioteca.usuario'
    _rec_name = 'nombre'
    
    nombre = fields.Char(string='Nombre', required=True)
    email = fields.Char(string='Email', required=True)
    direccion = fields.Char(string='Dirección', required=True)
    libros_prestados = fields.Char(string='Libros Prestados', required=True)
    cedula = fields.Char(string='Cédula')
    telefono = fields.Char(string='Teléfono')
    
    
#   @api.depends('firstname', 'lastname')
#   def _compute_display_name(self):
#       for record in self:
#           record.display_name =f"{record.firstname} - {record.lastname}"