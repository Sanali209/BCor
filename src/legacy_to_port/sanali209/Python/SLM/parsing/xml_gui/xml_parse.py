from typing import Union
from xml.dom import minidom

from loguru import logger

from SLM.appGlue.DAL.binding.bind import PropUser, BindingProperty
from SLM.parsing.param import ParamParser


class AttributeParser:
    """
    Represents an attribute of an XML element.
    """

    def __init__(self, name: str, value_type: type = None):
        self.name = name
        self.value = None
        self.required = False
        self.value_type = value_type

    def is_exist(self, xml_node):
        """
        Checks if the attribute exists in the XML node.
        """
        res = xml_node.hasAttribute(self.name)
        if self.required and not res:
            raise ValueError(f"Attribute {self.name} is required")
        return res

    def get_value(self, xml_node):
        """
        Extracts the attribute value from the XML node and converts it to the desired type.
        """
        self.value = xml_node.getAttribute(self.name)
        if self.value_type is not None:
            self.value = self.value_type(self.value)

    def process(self, xml_node):
        """
        Checks if the attribute exists and extracts its value if it does.
        """
        if self.is_exist(xml_node):
            self.get_value(xml_node)
            return True
        return False

    def set_element_attribute(self, parse_element):
        """
        Sets the attribute value on the corresponding element instance.
        """
        if self.value is None:
            return
        try:
            if isinstance(self.value, str) and self.value.startswith('read:self.'):
                self.value = self.get_atr_recursive(parse_element.parent_xml_parser.associated_object, self.value[10:])
            if isinstance(self.value, str) and self.value.startswith('bind:'):
                # example "bind:val"
                pars_str = self.value
                # todo improvement possible
                arg_parser = ParamParser(pars_str)
                source_prop_name=str(arg_parser.dict_param.get("bind"))
                prop_user:PropUser = parse_element.parent_xml_parser.associated_object.prop

                source_bind_prop:BindingProperty =getattr(prop_user.dispatcher,source_prop_name)
                target_obj = parse_element.associated_object
                source_bind_prop.bind(bind_target=target_obj,**arg_parser.dict_param)
                return

            setattr(parse_element.associated_object, self.name, self.value)
        except Exception as e:
            raise RuntimeError("something wrong")


    def get_atr_recursive(self, obj, atr_str):
        if '.' in atr_str:
            atr_str = atr_str.split('.')
            cur_obj = getattr(obj, atr_str[0])
            return self.get_atr_recursive(cur_obj, ",".join(atr_str[1:]))
        cur_obj = getattr(obj, atr_str)
        return cur_obj


class field_copy_attribute(AttributeParser):
    def __init__(self, name):
        super().__init__(name, str)

    def set_element_attribute(self, parse_element):
        if self.value is None:
            return
        obj_field = getattr(parse_element.parent_xml_parser.associated_object, self.value)
        setattr(parse_element.associated_object, self.name, obj_field)


class IdAttributeParser(AttributeParser):
    """
    Represents the "id" attribute.
    """

    def __init__(self):
        super().__init__("id")

    def set_element_attribute(self, parse_element):
        """
        Sets the "id" attribute on the element instance and registers it in the parser's GUI.
        """
        if self.value is None:
            return
        setattr(parse_element.parent_xml_parser.associated_object, self.value, parse_element.associated_object)


class ElementParser:
    """
    Represents a generic XML element and provides parsing logic.
    """

    def __init__(self, parent_xml_parser: Union['XMLParser', None],
                 parent_element_parser: Union['ElementParser', None],
                 xml_node):
        self.attributes: list[AttributeParser] = [IdAttributeParser()]
        self.xml_node = xml_node
        self.parent_xml_parser: 'XMLParser' = parent_xml_parser
        self.parent_element_parser: 'ElementParser' = parent_element_parser
        self.associated_object = None

    def parse(self):
        """
        Parses the element, including its attributes and child elements.
        """
        self.parse_attributes()
        self.process_associated_object()
        self.set_ass_obj_attributes()
        self.parse_sub_nodes()

    def process_associated_object(self):
        """
        Processes the associated object.
        """
        pass

    def set_ass_obj_attributes(self):
        """
        Sets the attribute values on the element instance.
        """
        for attribute in self.attributes:
            attribute.set_element_attribute(self)

    def parse_attributes(self):
        """
        Extracts attribute values from the XML node before creating the element instance.
        """
        for attribute in self.attributes:
            attribute.process(self.xml_node)

    def feed_text_node(self, node):
        pass

    def parse_sub_nodes(self):
        """
        Parses child elements recursively.
        """
        for child_node in self.xml_node.childNodes:
            if child_node.nodeType == child_node.TEXT_NODE:
                self.feed_text_node(child_node)
                continue
            if child_node.nodeType == child_node.ELEMENT_NODE:
                element_parser = self.parent_xml_parser.get_element_parser(child_node.nodeName)
                if element_parser is None:
                    logger.warning(f"Unknown element {child_node.nodeName}")
                    continue  # Skip unknown elements
                element_parser = element_parser(self.parent_xml_parser, self, child_node)
                element_parser.parse()


class XMLParser(ElementParser):
    """
    Parses an XML string and creates a GUI based on its structure.
    """
    element_parser = {}

    def __init__(self, xml_str: str):
        super().__init__(None, None, None)
        self.parent_xml_parser = self
        self.xml_str = xml_str

    def get_element_parser(self, element_name: str):
        """
        Returns a parser instance for the given element name.
        """
        return self.element_parser.get(element_name, None)

    def parse(self):
        """
        Parses the XML string and process associated object.
        """
        if self.xml_str is None:
            return
        xml_dom = minidom.parseString(self.xml_str)
        self.xml_node = xml_dom.documentElement
        super().parse()
        return self.associated_object
