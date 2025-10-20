# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging
import requests

logger = logging.getLogger(__name__) # Usar logger para ver errores/información en el log de Odoo

class BibliotecaLibro(models.Model):
    _name = 'biblioteca.libro'
    _description = 'Gestión de libros de la biblioteca'
    _rec_name = 'name'

    name = fields.Char(string='Título', required=True)
    isbn = fields.Char(string='ISBN')
    autor = fields.Many2one('biblioteca.autor', string='Autor') 
    genero = fields.Selection([
        ('ciencia_ficcion','Ciencia Ficción'),
        ('aventura','Aventura'),
        ('romance','Romance'),
        ('fantacia','Fantasía'),
        ('historica','Histórica'),
        ('filosofico','Filosófico'),
        ('politico','Político'),
        ('academico','Académico'),
        ('tragedia','Tragedia'),
        ('comedia','Comedia'),
        ('farsa','Farsa'),
    ], string='Género')
    a_pub = fields.Char(string='Año de publicación')
    descripcion = fields.Text(string='Descripción')
    portada_url = fields.Char(string='URL de Portada')
    portada_html = fields.Html('Vista previa', compute='_compute_portada_html')

    @api.depends('portada_url')
    def _compute_portada_html(self):
        for record in self:
            if record.portada_url:
                record.portada_html = f'<div style="text-align:center;"><img src="{record.portada_url}" style="max-height:200px;"/></div>'
            else:
                record.portada_html = ''

    @api.onchange('isbn')
    def _get_openlibrary_data(self):
        if self.isbn:
            url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{self.isbn}&format=json&jscmd=data"
            
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                key = f"ISBN:{self.isbn}"
                if key in data:
                    book_data = data[key]
                    
                    self.name = book_data.get('title', 'Título no encontrado')
                    self.a_pub = book_data.get('publish_date', False)
                    
                    covers = book_data.get('cover', {})
                    self.portada_url = covers.get('medium', False) or covers.get('small', False)
                    
                    authors_list = book_data.get('authors', [])
                    if authors_list:
                        author_name = authors_list[0].get('name')
                        if author_name:
                            author_obj = self.env['biblioteca.autor'].search([('autor', '=', author_name)], limit=1)
                            
                            if not author_obj:
                                author_obj = self.env['biblioteca.autor'].create({'autor': author_name})
                                logger.info(f"Autor creado: {author_name}")
                                
                            self.autor = author_obj.id
                    else:
                        self.autor = False
                        
                else:
                    logger.warning(f"ISBN {self.isbn} no encontrado en OpenLibrary.")
                    self.name = f"Libro no encontrado ({self.isbn})"
                    self.portada_url = False
                    self.a_pub = False
                    self.autor = False

            except requests.exceptions.RequestException as e:
                logger.error(f"Error al conectar con OpenLibrary para ISBN {self.isbn}: {e}")
                self.name = f"Error de API para ISBN: {self.isbn}"
                self.portada_url = False
                self.a_pub = False
                self.autor = False
            except Exception as e:
                logger.error(f"Error inesperado al procesar datos de OpenLibrary para ISBN {self.isbn}: {e}")
                self.name = f"Error interno para ISBN: {self.isbn}"
                self.portada_url = False
                self.a_pub = False
                self.autor = False
        else:
            self.name = False
            self.a_pub = False
            self.portada_url = False
            self.autor = False


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
    libro_id=fields.Many2one('biblioteca.libro', required=True)
    usuario_id = fields.Many2one('biblioteca.usuario', string='Usuario', required=True)
    fecha_devolucion= fields.Datetime()
    multa_bol = fields.Boolean(default=False)
    multa=fields.Float()
    fecha_maxima=fields.Datetime(compute='_compute_fecha_devolucion')
    usuario=fields.Many2one('res.users', string='Usuario presta', default= lambda self: self.env.uid)
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
            
            

def validar_cedula(cedula):
    if len(cedula) != 10 or not cedula.isdigit():
        return False

    provincia = int(cedula[:2])
    if provincia < 1 or provincia > 24:
        return False

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0

    for i in range(9):
        val = int(cedula[i]) * coeficientes[i]
        if val > 9:
            val -= 9
        total += val

    verificador = int(cedula[9])
    modulo = total % 10
    if modulo == 0:
        return verificador == 0
    else:
        return verificador == (10 - modulo)  
    
             
class biblioteca_Usuario(models.Model):
    _name ='biblioteca.usuario'
    _description = 'biblioteca.usuario'
    _rec_name = 'nombre'
    
    nombre = fields.Char(string='Nombre', required=True)
    email = fields.Char(string='Email', required=True)
    direccion = fields.Char(string='Dirección', required=True)
    libros_prestados = fields.Many2one('biblioteca.libro', string='Libro')
    cedula = fields.Char(string='Cédula', required=True)
    telefono = fields.Char(string='Teléfono')
    
    
    @api.constrains('cedula')
    def _check_cedula(self):
      for record in self:
        if record.cedula and not validar_cedula(record.cedula):
            raise ValidationError("Cédula inválida")