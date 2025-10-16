# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

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
            
            
            
class biblioteca_Prestamo(models.Model):
    _name ='biblioteca.prestamos'
    _description = 'biblioteca.prestamos'

    name= fields.Char( string='Prestamo')
    fecha_prestamo = fields.Datetime(default=datetime.now())
    libro_id=fields.Many2one('biblioteca.libro')
    usuario_id = fields.Many2one('biblioteca.usuario', string='Usuario')
    fecha_devolucion= fields.Datetime()
    multa_bol = fields.Boolean(default=False)
    multa=fields.Float()
    fecha_maxima=fields.Datetime(compute='_compute_fecha_devolucion')
    usuario=fields.Many2one('res.users', string='Usuario presta', default= lambda self: self.evn.uid)
    estado = fields.Selection([('b','Borrador'),
                               ('p','Prestado'),
                               ('m','Multa'),
                               ('d','Devuelto')],
                              string='Estado', default='b')

    @api.depends('fecha_maxima', 'fecha_prestamo')
    def _compute_fecha_devolucion(self):
        for record in self:
            record.fecha_maxima = record.fecha_prestamo + timedelta(days=2)
    
    
    def write(self, vals):
        seq= self.env.ref('biblioteca.sequence_codigo_prestamo').next_by_code('biblioteca.prestamo')
        vals['name']=seq
        return super(biblioteca_Prestamo, self).write(vals)
     
     
           
    def generar_prestamo(self):
        print("Generando prestamo")
        self.write({'estado':'p'})
        
        
        
class biblioteca_Multas(models.Model):
    _name ='biblioteca.multas'
    _description = 'biblioteca.multas'
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